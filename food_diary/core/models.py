from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from pymongo import MongoClient
from django.conf import settings

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
        
    def calculate_bmi(self):
        if self.height and self.weight:
            height_in_meters = self.height / 100
            return round(self.weight / (height_in_meters ** 2), 2)
        return None

    def calculate_recommended_calories(self):
        if self.weight and self.height and self.date_of_birth and self.gender:
            # Basic BMR calculation using Harris-Benedict equation
            age = (timezone.now().date() - self.date_of_birth).days // 365
            
            if self.gender == 'M':
                bmr = 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * age)
            else:
                bmr = 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * age)
                
            # Assuming moderate activity level (multiply by 1.55)
            return round(bmr * 1.55)
        return None

    def __str__(self):
        return self.username

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
