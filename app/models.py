from django.db import models

# Create your models here.
class User(models.Model):
    fname=models.CharField(max_length=100)
    lname=models.CharField(max_length=100)
    email=models.EmailField()
    mobile=models.PositiveIntegerField()
    address=models.CharField(max_length=100)
    zipcode=models.PositiveIntegerField()
    password=models.CharField(max_length=100) # confirm password only in html and view page not neewd to make coloumn
    profile=models.ImageField(upload_to='profile/',default="")
    usertype=models.CharField(max_length=100,default="buyer")
    
    def __str__(self):
        return self.fname+" "+self.lname  
    
class Contact(models.Model):
    fname=models.CharField(max_length=100)
    email=models.EmailField()
    subject=models.TextField()
    message=models.TextField()

    def __str__(self):
        return self.fname+" - "+self.email

class Product(models.Model):
    seller=models.ForeignKey(User,on_delete=models.CASCADE)
    choice1=(
        ("Men","Men"),
        ("Women","Women"),
        ("Kids","kids"),
        ("Accessories","Accessories"),
        ("Shoes","Shoes"),
        ("Goggles","Goggles"),
        ("Makeup","Makeup"),
        ("Furniture","Sandals"),
        ("Party Bulb","Party Bulb"),
        ("Kitchen tools","Kitchen tools"),

        )
    product_category=models.CharField(max_length=100,choices=choice1)
    product_name=models.CharField(max_length=100)
    product_price=models.PositiveIntegerField()
    product_desc=models.TextField()
    product_image=models.ImageField(upload_to="product_image",default="")

    def __str__(self):
        return self.seller.fname+" "+self.product_name
    
class Wishlist(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)

    def __str__(self):
        return self.user.fname+" - "+self.product.product_name
    
class Cart(models.Model):
    user=models.ForeignKey(User,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    product_price=models.PositiveIntegerField()
    product_qty=models.PositiveIntegerField(default=1)
    total_price=models.PositiveIntegerField()
    payment_status=models.BooleanField(default=False)

    def __str__(self):
        return self.user.fname+" - "+self.product.product_name



