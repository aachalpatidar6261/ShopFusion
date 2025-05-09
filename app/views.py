from dotenv import load_dotenv
import os
load_dotenv()
SHOPIFY_ACCESS_TOKEN=os.getenv("SHOPIFY_ACCESS_TOKEN")
SHOPIFY_STORE_URL =os.getenv("SHOPIFY_STORE_URL")


from django.shortcuts import render,redirect
from .models import *               # User,Contact,Product,Wishlist,Cart
from django.conf import settings
from django.core.mail import send_mail
import random
import stripe  # install stripe
from django.conf import settings
from django.http import JsonResponse,HttpResponse
from django.views.decorators.csrf import csrf_exempt
import json

import requests


# Create your views here.
stripe.api_key = settings.STRIPE_PRIVATE_KEY
YOUR_DOMAIN = 'http://localhost:8000'

def validate_signup(request):
    email=request.GET.get('email')
    data={
        'is_taken':User.objects.filter(email__iexact=email).exists()
         }
    return JsonResponse(data)

def validate_login(request):
    email=request.GET.get('email')
    data={
        'is_taken':User.objects.filter(email__iexact=email).exists()
         }
    return JsonResponse(data)

def validate_cp(request):
    user=User.objects.get(email=request.session['email']) 
    cp=request.GET.get('oldpassword')

    if user.password==cp:
        data={
        'is_taken':User.objects.filter(email__iexact=cp).exists()
         }
        return JsonResponse(data)
   


@csrf_exempt
def create_checkout_session(request):
	amount = int(json.load(request)['post_data'])
	final_amount=amount*100
	
	session = stripe.checkout.Session.create(
		payment_method_types=['card'],
		line_items=[{
			'price_data': {
				'currency': 'inr',
				'product_data': {
					'name': 'Checkout Session Data',
					},
				'unit_amount': final_amount,
				},
			'quantity': 1,
			}],
		mode='payment',
		success_url=YOUR_DOMAIN + '/success.html',
		cancel_url=YOUR_DOMAIN + '/cancel.html',)
	return JsonResponse({'id': session.id})

def success(request):
    user=User()
    try:
        user=User.objects.get(email=request.session['email'])
    except:
        pass
    carts=Cart.objects.filter(user=user,payment_status=False)
    for i in carts:
        i.payment_status=True
        i.save()
    carts=Cart.objects.filter(user=user,payment_status=False)
    request.session['cart_count']=len(carts)
    return render(request,'success.html')

def cancel(request):
	return render(request,'cancel.html')

def index(request):
    products=Product.objects.all()
    return render(request,'index.html',{'products':products})

def shop(request):
    products=Product.objects.filter(product_category="Women")
    return render(request,'shop.html',{'products':products})
    
def detail(request):
    products=Product.objects.all()
    return render(request,'detail.html',{'products':products})

def checkout(request):
    return render(request,'checkout.html')

def contact(request):
    if request.method=="POST":
        Contact.objects.create(
            fname=request.POST['fname'],
            email=request.POST['email'],
            subject=request.POST['subject'],
            message=request.POST['message'],
        )
        msg="Message Send Successfully"
        return render(request,'contact.html',{'msg':msg})
    else:
        return render(request,'contact.html')

def signup(request):
    if request.method=="POST":
        try:
            User.objects.get(email=request.POST['email'])
            msg="Email Already Exists"
            return render(request,'signup.html',{'msg':msg})
        except:
            if request.POST['password']==request.POST['cpassword']:
                User.objects.create(
                    fname=request.POST['fname'],
                    lname=request.POST['lname'],
                    email=request.POST['email'],
                    mobile=request.POST['mobile'],
                    address=request.POST['address'],
                    zipcode=request.POST['zipcode'],
                    password=request.POST['password'],
                    profile=request.FILES['profile'],
                    usertype=request.POST['usertype'],
                )
                msg="Email Register Successfully"
                return render(request,'login.html',{'msg':msg})
            else:
                msg="Password & Confirm Password Not Match"
                return render(request,'signup.html',{'msg':msg})
    else:
        return render(request,'signup.html')
    

def login(request):
    if request.method=="POST":
        try:
            user=User.objects.get(email=request.POST['email'])
            if user.password==request.POST['password']:
                if user.usertype=="buyer":
                    request.session['email']=user.email
                    request.session['fname']=user.fname
                    request.session['profile']=user.profile.url
                    wishlist=Wishlist.objects.filter(user=user)
                    request.session['wishlist_count']=len(wishlist)
                    cart=Cart.objects.filter(user=user,payment_status=False)
                    request.session['cart_count']=len(cart)
                    myorder=Cart.objects.filter(payment_status=True)
                    request.session['cart_count']=len(myorder)
                    return redirect('index')
                
                else:
                    request.session['email']=user.email
                    request.session['fname']=user.fname
                    request.session['profile']=user.profile.url
                    return redirect('seller-index')
            else:
                msg="Incorrect Password"
                return render(request,'login.html',{'msg':msg})
        except:
            msg="Email Not Register"
            return render(request,'signup.html',{'msg':msg})
    else:
        return render(request,'login.html')

def logout(request):
    try:
        del request.session['email']
        del request.session['fname']
        return redirect('logout')
    except:
        return render(request,'login.html')

def change_password(request):
    user=User.objects.get(email=request.session['email'])  
    if request.method=="POST":
        if user.password==request.POST['oldpassword']:
            if request.POST['newpassword']==request.POST['cnewpassword']:
                user.password=request.POST['newpassword']
                user.save()
                return redirect('logout')
            else:
                if user.usertype=="buyer":                    
                    msg="New Password & Confirm Password Does Not Matched"
                    return render(request,'change-password.html',{'msg':msg})
                else:
                    msg="New Password & Confirm Password Does Not Matched"
                    return render(request,'seller-change-password.html',{'msg':msg})
        else:
            if user.usertype=="buyer":
                msg="Incorrect Old Password"
                return render(request,'change-password.html',{'msg':msg})
            else:
                msg="Incorrect Old Password"
                return render(request,'seller-change-password.html',{'msg':msg})
                
    else:
        if user.usertype=="buyer":
            return render(request,'change-password.html')
        else:
            return render(request,'seller-change-password.html')
    
def forgot_password(request):
    if request.method=="POST":
        try:
            user=User.objects.get(email=request.POST['email'])
            otp=random.randint(1000,9999)
            subject = 'OTP For Forgot Password'
            message = "Hello "+user.fname+ " Your OTP Is "+ str(otp)
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email, ]
            send_mail( subject, message, email_from, recipient_list )
            return render(request,'otp.html',{'email':user.email,'otp':otp})
        except Exception as e:
            print(e)
            msg="Email Not Register"
            return render(request,'forgot-password.html',{'msg':msg})
    else:
        return render(request,'forgot-password.html')

def verify_otp(request):
    email=request.POST['email']
    otp=request.POST['otp']
    uotp=request.POST['uotp']

    if otp==uotp:        
        return render(request,'new-password.html')
    else:
        msg="Incorrect OTP"
        return render(request,'otp.html',{'msg':msg})
    
def new_password(request):
    email=request.POST['email']
    np=request.POST['newpassword']
    cnp=request.POST['cnewpassword']

    if np==cnp:
        user=User.objects.get(email=email)
        user.password=np
        user.save()
        return redirect('login')
    else:
        msg="New Password & Confirm New Password Does Not Matched"
        return render(request,'new-password.html',{'email':email,'msg':msg})

def profile(request):
    user=User.objects.get(email=request.session['email'])
    if request.method=="POST":
        user.fname=request.POST['fname']
        user.lname=request.POST['lname']
        user.email=request.POST['email']
        user.mobile=request.POST['mobile']
        user.address=request.POST['address']
        try:
            user.profile=request.FILES['profile']
        except:
            pass
        user.save()
        request.session['profile']=user.profile.url   # for header image
        msg="Profile Update Successfully"
        if user.usertype=="buyer":
            return render(request,'profile.html',{'msg':msg,'user':user})
        else:
            return render(request,'seller-profile.html',{'msg':msg,'user':user})
    else:
        if user.usertype=="buyer":
            return render(request,'profile.html',{'user':user})
        else:
            return render(request,'seller-profile.html',{'user':user})


def seller_index(request):
    return render(request,'seller-index.html')

def seller_add_product(request):
    seller=User.objects.get(email=request.session['email'])
    if request.method=="POST":
        Product.objects.create(
            seller=seller,
            product_category=request.POST['product_category'],
            product_name=request.POST['product_name'],
            product_price=request.POST['product_price'],
            product_desc=request.POST['product_desc'],
            product_image=request.FILES['product_image'],
        )
        msg="Product Added Successfully"
        return render(request,'seller-add-product.html',{'msg':msg})
    else:
        return render(request,'seller-add-product.html')

def seller_view_product(request):
    seller=User.objects.get(email=request.session['email'])
    products=Product.objects.filter(seller=seller)
    return render(request,'seller-view-product.html',{'products':products})

    

def seller_view_detail(request,pk):
    product=Product.objects.get(pk=pk)
    return render(request,'seller-view-detail.html',{'product':product})

def seller_edit_product(request,pk):
    seller=User.objects.get(email=request.session['email'])
    product=Product.objects.get(pk=pk)
    if request.method=="POST":
        product.product_category=request.POST['product_category']
        product.product_name=request.POST['product_name']
        product.product_price=request.POST['product_price']
        product.product_desc=request.POST['product_desc']
        try:
            product.product_image=request.FILES['product_image']
        except:
            pass
        product.save()
        msg="Product Update Successfully"
        return render(request,'seller-edit-detail.html',{'product':product,'msg':msg})
    else:
        return render(request,'seller-edit-detail.html',{'product':product})
    
def seller_delete_product(request,pk):
    product=Product.objects.get(pk=pk)
    product.delete()
    return redirect('seller-view-product')

def view_detail(request,pk):
    wishlist_flag=False
    cart_flag=False
    product=Product.objects.get(pk=pk)
    try:
        user=User.objects.get(email=request.session['email'])
        try:
            Cart.objects.get(user=user,product=product,payment_statuc=False)
            cart_flag=True
        except:
            pass
        
        try:
            Wishlist.objects.get(user=user,product=product)
            wishlist_flag=True
        except:
            pass
        return render(request,'view-detail.html',{'product':product,'wishlist_flag':wishlist_flag,'cart_flag':cart_flag})
    except:
        return render(request,'view-detail.html',{'product':product})

   
def add_to_wishlist(request, pk):
    product=Product.objects.get(pk=pk)
    user=User.objects.get(email=request.session['email'])
    Wishlist.objects.create(
        user=user,
        product=product
    )
    return redirect('wishlist')

def wishlist(request):
    try:
        user=User.objects.get(email=request.session['email'])
        wishlist=Wishlist.objects.filter(user=user)
        request.session['wishlist_count']=len(wishlist)
        return render(request,"wishlist.html",{'wishlist':wishlist})

    except:
    
        return render(request,'login.html')

def remove_from_wishlist(request, pk):
    product=Product.objects.get(pk=pk)
    user=User.objects.get(email=request.session['email'])
    wishlist=Wishlist.objects.filter(user=user,product=product)
    wishlist.delete()
    return redirect('wishlist')

def add_to_cart(request, pk):
    product=Product.objects.get(pk=pk)
    user=User.objects.get(email=request.session['email'])
    Cart.objects.create(
        user=user,
        product=product,
        product_price=product.product_price,
        product_qty=1,
        total_price=product.product_price,
    )
    return redirect('cart')

def cart(request):
    net_price=0
    user=User.objects.get(email=request.session['email'])
    cart=Cart.objects.filter(user=user,payment_status=False)
    request.session['cart_count']=len(cart)
    for i in cart:
        net_price=net_price+i.total_price
    return render(request,"cart.html",{'cart':cart,'net_price':net_price})

def remove_from_cart(request, pk):
    product=Product.objects.get(pk=pk)
    user=User.objects.get(email=request.session['email'])
    cart=Cart.objects.get(user=user,product=product,payment_status=False)
    cart.delete()
    return redirect('cart')

def change_qty(request):
    pk=int(request.POST['pk']) # from data always return in string format so we use int.
    cart=Cart.objects.get(pk=pk)
    product_qty=int(request.POST['product_qty'])
    cart.product_qty=product_qty
    cart.total_price=cart.product_price*product_qty
    cart.save()
    return redirect('cart')

def myorder(request):
    try:
        user=User.objects.get(email=request.session['email'])
        cart=Cart.objects.filter(user=user,payment_status=True)
        return render(request,'myorder.html',{'cart':cart})
    except:
        msg="PLEASE, Signup"
        return render(request,'myorder.html')


def seller_view_order(request):
    myorder=[]
    seller=User.objects.get(email=request.session['email'])
    cart=Cart.objects.filter(payment_status=True)
    for i in cart:
        if i.product.seller == seller:
            myorder.append(i)
    myorder=Cart.objects.filter(payment_status=False)
    request.session['cart_count']=len(myorder)
    return render(request,'seller_view_order.html',{'myorder':myorder})

def women(request):
    products=Product.objects.filter(product_category="Women")
    return render(request,'shop.html',{'products':products})

def men(request):
    products=Product.objects.filter(product_category="Men")
    return render(request,'shop.html',{'products':products})

def kids(request):
    products=Product.objects.filter(product_category="Kids")
    return render(request,'shop.html',{'products':products})

def accesseries(request):
    products=Product.objects.filter(product_category="Accessories")
    return render(request,'shop.html',{'products':products})

def shoes(request):
    products=Product.objects.filter(product_category="Shoes")
    return render(request,'shop.html',{'products':products})

def Goggles(request):
    products=Product.objects.filter(product_category="Goggles")
    return render(request,'shop.html',{'products':products})

def Makeup(request):
    products=Product.objects.filter(product_category="Makeup")
    return render(request,'shop.html',{'products':products})

def Party_Bulb(request):
    products=Product.objects.filter(product_category="Party Bulb")
    return render(request,'shop.html',{'products':products})

def Furniture(request):
    products=Product.objects.filter(product_category="Furniture")
    return render(request,'shop.html',{'products':products})

def Kitchen_tools(request):
    products=Product.objects.filter(product_category="Kitchen tools")
    return render(request,'shop.html',{'products':products})




def Sync_products_to_shopify(request):
    print("sync_products_to_shopify-------------123-")
    products = Product.objects.all()
    print(products)
    if not products:
        return JsonResponse({"error": "No products found in Django."})

    for product in products:
        url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/products.json"
        headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN, "Content-Type": "application/json"}
        # Shopify Product Data Format
        payload = {
            "product": {
                "title":product.product_name,
                "vendor":"Eco-Central",
                "Category" : product.product_category,
                "Product_type" : "General_ByECO",
                "variants":[{"price":str(product.product_price)}],
            }
        }        
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 201:
            print(f"Failed to add product: {product.product_name}")
            print(response.json())  # ✅ Debugging: Print Shopify response

    return JsonResponse({"message": "Products synced to Shopify!"})


def get_shopify_product(request): 
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/products.json"
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN}
    response = requests.get(url, headers=headers)   
    # print(response.text)  #
    if response.status_code == 200:
        # data = response.json() # .json() converts the raw response into a Python dictionary.
        products = response.json().get("products", []) # This line safely extracts the "products" list from the data dictionary. If "products" key exists → you get the list of products.
        return render(request, "get_shopify_product.html", {"products":products})
    else:
        return JsonResponse({"error": "Failed to fetch products"}, status=response.status_code)

def update_shopify_product_data(request, product_id):
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN, "Content-Type": "application/json"}

    if request.method == "POST":
        title = request.POST['title']
        price = request.POST['price']
        variants = [{"price": price}]        
        vendor = request.POST['vendor']
        
        update_data={   
            "product":{
                "id" : product_id,
                "title" : title,
                "variants" : variants,
                "vendor" : vendor              
            }
        }

        url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/products/{product_id}.json"
        response = requests.put(url, headers=headers, json=update_data)
        try:
            if response.status_code == 200:
                return redirect("get_shopify_product")
        except Exception as x:
            print("Exception : ",x,{"error": "Failed to fetch products--------------------"}, status=response.status_code)            
    else:
        url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/products/{product_id}.json"
        response = requests.get(url, headers=headers)   
        if response.status_code == 200:
            product = response.json().get("product", {})
            
            context = {
                "product_id" : product.get("id"),
                "title" : product.get("title"),
                "price" : product['variants'][0]['price'],
                "vendor" : product.get("vendor")
            }         
            # print(product.get("id"), product.get("title"),product.get("vendor"),product['variants'][0]['price'])
            # print("------------------------dict : ",context['product_id'],context['title'], context['vendor'],context['price'][0]['price'])
            return render(request, "update_shopify_product_data.html",{"context" : context})
        else:
            msg = "MSG : Product not found"
            return render(request, 'update_shopify_product_data.html', {"msg" : msg})
        
def delete_shopify_product(request, product_id):
    print("enter : delete veiw--------------")
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN, "Content-Type": "application/json"}
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/products/{product_id}.json"
    response = requests.delete(url, headers=headers)

    if response.status_code == 200 or response.status_code == 400:
        return JsonResponse({"msg" : "Product Deleted form Shopify Successfully!"})
    else:
        return JsonResponse({"error": "Failed to delete product"})

# CRUD all are work.

def create_order_in_shopify(request):
    print("enter : Order veiw--------------")    
    headers = {"X-Shopify-Access-Token": SHOPIFY_ACCESS_TOKEN, "Content-Type": "application/json"}
    url = f"https://{SHOPIFY_STORE_URL}/admin/api/2024-01/orders.json"

    if request.method == "POST":
        print("enter in post method in create_order_in_shopify")
        try:
            print("try block!")
            # data = json.loads(requests.body)
            # print(data,"data in try block!")
            quality = request.POST.get('quality')
            name = request.POST.get('name')
            email = request.POST.get('email')
            address = request.POST.get('address')
            phone = request.POST.get('phone')
            variant_id = random.randint(9000000,200000000),
            variant_id = int(variant_id[0])
            print(quality, name, email,address, phone, variant_id, "details ------------------***")
        except json.JSONDecodeError:
            print("except block!")
            return JsonResponse({'error': 'Invalid or empty JSON'}, status=400)
        
        print("above order '4567'-------------------")
        order_data = {
            "order" : {
                "line_item" : [
                    {
                        "variant_id" : variant_id,
                        # int(data["order"]["line_item"][0]["variant_id"]),
                        "quality" : quality
                    }
                ],
                "customer" : {
                    "name": name,
                    "email": email,
                },
                "billing_address" : {
                    "name": name,
                    "address": address,
                    "phone": phone           
                },
                "shipping_address": {
                    "name": name,
                    "address": address,
                    "phone": phone
                },
                #  "financial_status": "paid"
            }
        }
        print("=======================order data : ", order_data)
        try:
            print("=======================order try yeahh.")
            response = requests.post(url, headers=headers, data=json.dumps(order_data))
            print("response : ",response)
            if response.status_code == 201:
                print("response.status_code: ",response.status_code)
                # res = response.json()
                msg = "Order for Shopify Store is Created!"
                return response(request, "create_order_in_shopify.html", {'msg':msg})
            
        except Exception as ex:
            print(ex,"Order for Shopify Store is not Created! XXXXXXXXXXXXX_________________")
            return render(request, "create_order_in_shopify.html")
        
    else:
        print("method failed!-------------------")
        return render(request, "create_order_in_shopify.html")