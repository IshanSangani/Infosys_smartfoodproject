from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from pymongo import MongoClient
from django.conf import settings
from django.contrib.auth import get_user_model
from djongo import models as djongo_models
from bson import ObjectId

class CustomUser(AbstractUser):
    # Additional fields for user profile
    date_of_birth = models.DateField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)  # in cm
    weight = models.FloatField(null=True, blank=True)  # in kg
    gender = models.CharField(max_length=10, choices=[
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other')
    ], null=True, blank=True)
    daily_calorie_goal = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'  # MongoDB collection name
        
   

    def __str__(self):
        return self.username

class FoodEntry(djongo_models.Model):
    _id = djongo_models.ObjectIdField()
    user_id = djongo_models.CharField(max_length=100)
    date_added = djongo_models.DateTimeField(default=timezone.now)
    image_url = djongo_models.URLField(max_length=500)
    food_name = djongo_models.CharField(max_length=100)
    confidence = djongo_models.FloatField()
    calories = djongo_models.FloatField()
    proteins = djongo_models.FloatField()
    carbs = djongo_models.FloatField()
    fat = djongo_models.FloatField()
    fiber = djongo_models.FloatField()
    sugar = djongo_models.FloatField()
    ingredients = djongo_models.JSONField(null=True, blank=True)
    api_response = djongo_models.JSONField(null=True, blank=True)

    class Meta:
        db_table = 'food_entries'

    def __str__(self):
        return f"{self.user.username} - {self.food_name} ({self.date_added})"

def initialize_mongodb_collections():
    try:
        client = MongoClient('mongodb://localhost:27017/')
        db = client['food_diary_db']
        
        # Create collections if they don't exist
        if 'users' not in db.list_collection_names():
            db.create_collection('users')
        
        # Add any indexes you need
        db.users.create_index('username', unique=True)
        
        print("MongoDB collections initialized successfully!")
    except Exception as e:
        print(f"Error initializing MongoDB collections: {str(e)}")

# Call this function when your app starts
initialize_mongodb_collections()
