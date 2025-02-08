from pprint import pprint
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError


class DynamoDBService:
    def __init__(self, region_name: str, aws_access_key_id: str, aws_secret_access_key: str, dynamo_table_name: str):
        self.dynamodb = boto3.resource(
            "dynamodb",
            region_name=region_name,
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key
        )
        self.table_name = dynamo_table_name
        self.table = self.dynamodb.Table(self.table_name)

        pprint({"INFO": f"Connected to DynamoDB table: {self.table_name}"})

    def get_user(self, user_id: int):
        user_id = str(user_id)

        try:
            response = self.table.get_item(Key={"user_id": user_id})
            return response.get("Item")
        except (BotoCoreError, NoCredentialsError) as e:
            pprint({"ERROR": f"Error fetching user from {self.table_name}: {str(e)}"})
            return None

    def save_user(self, user_id: int, phone_number: str, first_name: str, last_name: str):
        existing_user = self.get_user(user_id)
        if existing_user:
            pprint({"INFO": f"User {user_id} already exists."})
            return existing_user

        user_id = str(user_id)
        phone_number = str(phone_number)

        try:
            new_user = {
                "user_id": user_id,
                "phone": phone_number,
                "first_name": first_name or "",
                "last_name": last_name or "",
                "survey_completed": False
            }
            response = self.table.put_item(Item=new_user)
            status_code = response.get("ResponseMetadata", {}).get("HTTPStatusCode")
            if status_code == 200:
                pprint({"INFO": f"New user {user_id} saved to {self.table_name}."})
                return new_user
            pprint({"WARNING": "DynamoDB did not return 200 for put_item."})
            return None
        except (BotoCoreError, NoCredentialsError) as e:
            pprint({"ERROR": f"Error saving user to {self.table_name}: {str(e)}"})
            return None

    def update_survey(self, user_id: int, survey_data: dict):
        print(survey_data)
        user_id = str(user_id)

        try:
            self.table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="""
                    SET #sty = :sty,
                        #colors = :cls,
                        #brands = :br,
                        #gender = :g,
                        #ht = :h,
                        #wt = :w,
                        survey_completed = :sc
                """,
                ExpressionAttributeNames={
                    "#sty": "style",
                    "#colors": "colors",
                    "#brands": "brands",
                    "#gender": "gender",
                    "#ht": "height",
                    "#wt": "weight"
                },
                ExpressionAttributeValues={
                    ":sty": survey_data.get("style", ""),
                    ":cls": survey_data.get("colors", ""),
                    ":br": survey_data.get("brands", ""),
                    ":g": survey_data.get("gender", ""),
                    ":h": survey_data.get("height", ""),
                    ":w": survey_data.get("weight", ""),
                    ":sc": True
                }
            )
            pprint({"INFO": f"Survey updated for user {user_id} in {self.table_name}."})
        except (BotoCoreError, NoCredentialsError) as e:
            pprint({"ERROR": f"Error updating survey for {user_id} in {self.table_name}: {str(e)}"})

    def update_wardrobe(self, user_id: int, s3_key: str, summary: str):
        user_id = str(user_id)

        try:
            response = self.table.update_item(
                Key={"user_id": user_id},
                UpdateExpression="SET wardrobe = list_append(if_not_exists(wardrobe, :empty_list), :new_item)",
                ExpressionAttributeValues={
                    ":new_item": [{"s3_key": s3_key, "summary": summary}],
                    ":empty_list": [],
                },
                ReturnValues="UPDATED_NEW"
            )
            pprint(f"Wardrobe updated for user {user_id}. Added item: {s3_key}")
            return response
        except (BotoCoreError, NoCredentialsError) as e:
            pprint(f"Error updating wardrobe for user {user_id}: {e}")
            return None
