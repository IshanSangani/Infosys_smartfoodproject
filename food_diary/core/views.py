from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser
from django.conf import settings
from pymongo import MongoClient
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def home(request):
    return render(request, 'index.html')

def signup(request):
    if request.method == "POST":
        username = request.POST.get('username')
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        pass1 = request.POST.get('pass1')
        pass2 = request.POST.get('pass2')

        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Username already exists!")
            return redirect('signup')
        
        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('signup')
        
        if pass1 != pass2:
            messages.error(request, "Passwords do not match!")
            return redirect('signup')

        user = CustomUser.objects.create_user(username=username, email=email, password=pass1)
        user.first_name = fname
        user.last_name = lname
        user.save()

        messages.success(request, "Account created successfully!")
        return redirect('signin')

    return render(request, 'signup.html')

def signin(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('pass1')

        user = authenticate(username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials!")
            return redirect('signin')

    return render(request, 'signin.html')

@login_required
def signout(request):
    logout(request)
    messages.success(request, "Logged out successfully!")
    return redirect('home')

def test_mongodb_connection():
    try:
        
        client = MongoClient('mongodb://localhost:27017/')
        
        db = client['food_diary_db']
        
        
        users_collection = db['users']
        
        
        test_doc = {"test": "connection"}
        users_collection.insert_one(test_doc)
        
       
        users_collection.delete_one({"test": "connection"})
        
        print("MongoDB connection successful!")
        return True
    except Exception as e:
        print(f"MongoDB connection failed: {str(e)}")
        return False

def test_mongodb(request):
    try:
        
        client = MongoClient('mongodb://localhost:27017/')
        
        
        db = client['food_diary_db']
        
        
        db.command('ping')
        
        
        collections = db.list_collection_names()
        
        return HttpResponse(
            f"MongoDB Connection Successful!<br>"
            f"Database: food_diary_db<br>"
            f"Collections: {', '.join(collections)}"
        )
    except Exception as e:
        return HttpResponse(f"MongoDB Connection Failed: {str(e)}")

@login_required
def dashboard(request):
    return render(request, 'dashboard.html')



