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
from .ml_model import FoodClassifier
from pathlib import Path
from PIL import Image
import io

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

# Initialize the classifier
food_classifier = FoodClassifier()

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


@login_required
def dashboard(request):
    try:
        food_items = []
        image_url = None
        
        if request.method == 'POST' and request.FILES.get('food_image'):
            print("POST request received")
            image_file = request.FILES['food_image']
            
            # Create paths
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_food.jpg"
            relative_path = f'food_images/user_{request.user.id}/{filename}'
            absolute_path = Path(settings.MEDIA_ROOT) / 'food_images' / f'user_{request.user.id}'
            
            try:
                # Ensure directory exists
                absolute_path.mkdir(parents=True, exist_ok=True)
                
                # Read and validate image
                image_data = image_file.read()
                image = Image.open(io.BytesIO(image_data))
                
                # Save the image
                saved_path = default_storage.save(relative_path, ContentFile(image_data))
                image_url = default_storage.url(saved_path)
                
                # Get prediction
                prediction = food_classifier.predict(image_data)
                print(f"Prediction result: {prediction}")
                
                if prediction and isinstance(prediction, dict):
                    # Create food item for display
                    food_items.append({
                        'name': prediction.get('food_name', 'Unknown Food'),
                        'grade': f"{prediction.get('confidence', 0.0):.0%}",
                        'nutrition': prediction.get('nutrition', {})
                    })
                    
                    # Save to MongoDB
                    food_entry = {
                        'user_id': str(request.user.id),
                        'date_added': timezone.now(),
                        'image_url': image_url,
                        'food_name': prediction.get('food_name', 'Unknown Food'),
                        'confidence': prediction.get('confidence', 0.0),
                        'calories': prediction.get('nutrition', {}).get('calories', 0.0),
                        'proteins': prediction.get('nutrition', {}).get('proteins', 0.0),
                        'carbs': prediction.get('nutrition', {}).get('carbs', 0.0),
                        'fat': prediction.get('nutrition', {}).get('fat', 0.0),
                        'fiber': prediction.get('nutrition', {}).get('fiber', 0.0),
                        'sugar': prediction.get('nutrition', {}).get('sugar', 0.0),
                        'ingredients': [],
                        'api_response': prediction
                    }
                    
                    # Save to MongoDB using FoodEntry model
                    entry = FoodEntry(**food_entry)
                    entry.save()
                    
                    messages.success(request, f"Detected {prediction['food_name']} with {prediction['nutrition']['calories']} calories!")
                    
                    # Redirect after successful POST to prevent form resubmission
                    return redirect('dashboard')
                else:
                    messages.warning(request, "Could not analyze the food image.")
                    
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                messages.error(request, "Error processing the image.")
        
        # Get recent entries from MongoDB
        recent_entries = FoodEntry.objects.filter(
            user_id=str(request.user.id)
        ).order_by('-date_added')
        
        context = {
            'food_items': food_items,
            'recent_entries': recent_entries,
            'debug': settings.DEBUG
        }
        
        return render(request, 'dashboard.html', context)
        
    except Exception as e:
        logger.error(f"Error in dashboard view: {str(e)}")
        messages.error(request, "An error occurred while processing your request.")
        return render(request, 'dashboard.html', {
            'food_items': [],
            'recent_entries': [],
            'debug': settings.DEBUG
        })



