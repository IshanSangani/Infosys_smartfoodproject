from ultralytics import YOLO
from PIL import Image
import io
import os

class FoodClassifier:
    def __init__(self):
        try:
            model_path = os.path.join(os.path.dirname(__file__), 'model.pt')
            print(f"Loading model from: {model_path}")
            self.model = YOLO(model_path)
            
            # Print model's classes
            print("\nModel's available classes:")
            print(self.model.names)
            
            # Define nutrition data for all possible classes
            self.nutrition_database = {
                'Apple': {
                    'calories': 52.0,
                    'proteins': 0.3,
                    'carbs': 14.0,
                    'fat': 0.2,
                    'fiber': 2.4,
                    'sugar': 10.4
                },
                'Chapathi': {
                    'calories': 120.0,
                    'proteins': 3.0,
                    'carbs': 20.0,
                    'fat': 3.5,
                    'fiber': 1.0,
                    'sugar': 0.0
                },
                'Chicken Gravy': {
                    'calories': 190.0,
                    'proteins': 20.0,
                    'carbs': 4.0,
                    'fat': 11.0,
                    'fiber': 0.5,
                    'sugar': 1.0
                },
                'Fries': {
                    'calories': 312.0,
                    'proteins': 3.4,
                    'carbs': 41.0,
                    'fat': 15.0,
                    'fiber': 3.8,
                    'sugar': 0.3
                },
                'Idli': {
                    'calories': 39.0,
                    'proteins': 2.0,
                    'carbs': 8.0,
                    'fat': 0.1,
                    'fiber': 0.6,
                    'sugar': 0.0
                },
                'Pizza': {
                    'calories': 266.0,
                    'proteins': 11.0,
                    'carbs': 33.0,
                    'fat': 10.0,
                    'fiber': 2.3,
                    'sugar': 3.6
                },
                'Rice': {
                    'calories': 130.0,
                    'proteins': 2.7,
                    'carbs': 28.0,
                    'fat': 0.3,
                    'fiber': 0.4,
                    'sugar': 0.1
                },
                'Soda': {
                    'calories': 41.0,
                    'proteins': 0.0,
                    'carbs': 10.6,
                    'fat': 0.0,
                    'fiber': 0.0,
                    'sugar': 10.6
                },
                'Tomato': {
                    'calories': 18.0,
                    'proteins': 0.9,
                    'carbs': 3.9,
                    'fat': 0.2,
                    'fiber': 1.2,
                    'sugar': 2.6
                },
                'Vada': {
                    'calories': 97.0,
                    'proteins': 3.4,
                    'carbs': 12.8,
                    'fat': 4.2,
                    'fiber': 1.1,
                    'sugar': 0.0
                },
                'banana': {
                    'calories': 89.0,
                    'proteins': 1.1,
                    'carbs': 23.0,
                    'fat': 0.3,
                    'fiber': 2.6,
                    'sugar': 12.2
                },
                'burger': {
                    'calories': 295.0,
                    'proteins': 17.0,
                    'carbs': 24.0,
                    'fat': 14.0,
                    'fiber': 1.3,
                    'sugar': 4.4
                }
            }
            
        except Exception as e:
            print(f"Error loading model: {str(e)}")
            raise Exception(f"Failed to load model: {str(e)}")

    def predict(self, image_data):
        try:
            # Open image from bytes
            img = Image.open(io.BytesIO(image_data))
            
            # Make prediction
            results = self.model(img)
            
            # Process results
            if len(results) > 0:
                # Get all detections
                boxes = results[0].boxes
                
                if len(boxes) > 0:
                    # Get the highest confidence detection
                    box = boxes[0]
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    predicted_class = results[0].names[class_id]
                    
                    print(f"\nDetected: {predicted_class} with confidence {confidence:.2f}")
                    
                    # Get nutrition data - try exact match first, then case-insensitive
                    nutrition = self.nutrition_database.get(predicted_class) or \
                               self.nutrition_database.get(predicted_class.title()) or \
                               self.nutrition_database.get(predicted_class.lower()) or \
                               {
                                   'calories': 0.0,
                                   'proteins': 0.0,
                                   'carbs': 0.0,
                                   'fat': 0.0,
                                   'fiber': 0.0,
                                   'sugar': 0.0
                               }
                    
                    print(f"Nutrition data: {nutrition}")  # Debug print
                    
                    return {
                        'food_name': predicted_class,
                        'confidence': confidence,
                        'nutrition': nutrition
                    }
            
            print("No food detected in image")
            return {
                'food_name': 'Unknown Food',
                'confidence': 0.0,
                'nutrition': {
                    'calories': 0.0,
                    'proteins': 0.0,
                    'carbs': 0.0,
                    'fat': 0.0,
                    'fiber': 0.0,
                    'sugar': 0.0
                }
            }
            
        except Exception as e:
            print(f"Error in prediction: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                'food_name': 'Error',
                'confidence': 0.0,
                'nutrition': {
                    'calories': 0.0,
                    'proteins': 0.0,
                    'carbs': 0.0,
                    'fat': 0.0,
                    'fiber': 0.0,
                    'sugar': 0.0
                }
            }