from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import CustomUser, FoodEntry
from django.conf import settings
from pymongo import MongoClient
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
import requests
from django.conf import settings
import tempfile
import os
import logging
import json
from datetime import datetime
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.utils import timezone
from bson import ObjectId

# Create a custom filter to exclude MongoDB logs
class NoMongoFilter(logging.Filter):
    def filter(self, record):
        return not any(x in record.getMessage() for x in [
            'MongoClient', 
            'sql_command:', 
            'params:', 
            'Find query:', 
            'Result:', 
            'update_many:', 
            'inserted ids'
        ])

# Set up logging with custom filter
logger = logging.getLogger('food_diary')
logger.setLevel(logging.INFO)

# Create handlers
console_handler = logging.StreamHandler()
file_handler = logging.FileHandler('api_debug.log')

# Set levels
console_handler.setLevel(logging.INFO)
file_handler.setLevel(logging.DEBUG)

# Create formatters
console_formatter = logging.Formatter('%(message)s')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Add formatters to handlers
console_handler.setFormatter(console_formatter)
file_handler.setFormatter(file_formatter)

# Add filter to console handler
console_handler.addFilter(NoMongoFilter())

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)

# Remove any existing handlers from root logger to avoid duplicate logs
logging.getLogger('root').handlers = []

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
    try:
        recent_entries = FoodEntry.objects.filter(user_id=str(request.user.id)).order_by('-date_added')
        context = {
            'recent_entries': recent_entries,
            'debug': settings.DEBUG
        }
        
        if request.method == 'POST' and request.FILES.get('food_image'):
            image_file = request.FILES['food_image']
            logger.info(f"Processing image: {image_file.name}")
            
            try:
                # Read the image content directly from the uploaded file
                image_content = image_file.read()
                
                # Create a simple filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                extension = '.jpg'  # Default to jpg
                if image_file.name.lower().endswith('.png'):
                    extension = '.png'
                
                safe_filename = f"{timestamp}_food{extension}"
                file_path = f'food_images/user_{request.user.id}/{safe_filename}'
                
                # Save image directly from content
                saved_path = default_storage.save(file_path, ContentFile(image_content))
                image_url = default_storage.url(saved_path)
                
                # Make API request
                url = "https://vision.foodvisor.io/api/1.0/en/analysis/"
                headers = {"Authorization": f"Api-Key {settings.FOODVISOR_API_KEY}"}
                
                logger.info("Sending request to Foodvisor API...")
                files = {'image': (safe_filename, image_content, 'image/jpeg')}
                response = requests.post(url, headers=headers, files=files)
                
                logger.info(f"API Response Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"API Response Data: {data}")
                    
                    # Get the first food item
                    if data.get('items') and data['items'][0].get('food'):
                        food_item = data['items'][0]['food'][0]
                        food_info = food_item.get('food_info', {})
                        nutrition = food_info.get('nutrition', {})
                        
                        # Calculate total nutritional values from all ingredients
                        total_calories = 0
                        total_proteins = 0
                        total_carbs = 0
                        total_fat = 0
                        total_fiber = 0
                        total_sugar = 0
                        
                        ingredients_list = []
                        
                        # Process each ingredient
                        for ingredient in food_item.get('ingredients', []):
                            ing_info = ingredient.get('food_info', {})
                            ing_nutrition = ing_info.get('nutrition', {})
                            quantity_factor = ingredient.get('quantity', 0) / 100.0  # Convert to percentage
                            
                            # Add to totals
                            total_calories += ing_nutrition.get('calories_100g', 0) * quantity_factor
                            total_proteins += ing_nutrition.get('proteins_100g', 0) * quantity_factor
                            total_carbs += ing_nutrition.get('carbs_100g', 0) * quantity_factor
                            total_fat += ing_nutrition.get('fat_100g', 0) * quantity_factor
                            total_fiber += ing_nutrition.get('fibers_100g', 0) * quantity_factor
                            total_sugar += ing_nutrition.get('sugars_100g', 0) * quantity_factor
                            
                            # Add to ingredients list
                            ingredients_list.append({
                                'name': ing_info.get('display_name', 'Unknown'),
                                'quantity': ingredient.get('quantity', 0)
                            })
                        
                        # Create new food entry with calculated values
                        food_entry = FoodEntry(
                            user_id=str(request.user.id),
                            image_url=image_url,
                            food_name=food_info.get('display_name', 'Unknown Food'),
                            quantity=food_item.get('quantity', 0.0),
                            grade=food_info.get('fv_grade', 'N/A'),
                            calories=total_calories,
                            proteins=total_proteins,
                            carbs=total_carbs,
                            fat=total_fat,
                            fiber=total_fiber,
                            sugar=total_sugar,
                            ingredients=ingredients_list,
                            api_response=data
                        )
                        food_entry.save()
                        
                        messages.success(request, "Food analysis completed successfully!")
                        return redirect('dashboard')
                    else:
                        messages.warning(request, "No food items detected in the image.")
                else:
                    logger.error(f"API Error: {response.status_code} - {response.text}")
                    messages.error(request, f"API Error: {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error processing image: {str(e)}")
                messages.error(request, f"Error processing image: {str(e)}")
                
        return render(request, 'dashboard.html', context)
                
    except Exception as e:
        logger.error(f"Error retrieving entries: {str(e)}")
        messages.error(request, "Error retrieving entries")
        context = {
            'recent_entries': [],
            'debug': settings.DEBUG
        }
        return render(request, 'dashboard.html', context)

def verify_food_entries(request):
    if not request.user.is_authenticated:
        return HttpResponse("Not authenticated")
    
    # Get all entries for debugging
    all_entries = FoodEntry.objects.all()
    output = []
    
    output.append(f"Current user ID: {request.user.id}")
    output.append(f"Total entries in database: {all_entries.count()}")
    
    for entry in all_entries:
        output.append(f"Entry ID: {entry._id}")
        output.append(f"User ID: {entry.user_id}")
        output.append(f"Food Name: {entry.food_name}")
        output.append(f"Date Added: {entry.date_added}")
        output.append("---")
    
    return HttpResponse("<br>".join(output))



