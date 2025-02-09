import base64
import io
import uuid
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from pprint import pprint


class S3ImageStorage:
    def __init__(self, region_name: str, bucket_name: str):
        self.s3_client = boto3.client(
            "s3",
            region_name=region_name,
        )
        self.bucket_name = bucket_name
        self.region_name = region_name
        pprint({"INFO": f"S3ImageStorage initialized with bucket={self.bucket_name}, region={region_name}"})

    def upload_user_photo(self, user_id: int, image_bytes: bytes, extension: str = "jpg", public: bool = False) -> dict:
        unique_filename = f"photo_{uuid.uuid4()}.{extension}"
        s3_key = f"user_{user_id}/{unique_filename}"

        file_obj = io.BytesIO(image_bytes)
        extra_args = {
            "ContentType": f"image/{extension}"
        }
        if public:
            extra_args["ACL"] = "public-read"

        try:
            self.s3_client.upload_fileobj(
                Fileobj=file_obj,
                Bucket=self.bucket_name,
                Key=s3_key,
                ExtraArgs=extra_args
            )
            pprint({"INFO": f"Uploaded photo to s3://{self.bucket_name}/{s3_key}"})

            public_url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_key}" if public else None
            return {
                "s3_key": s3_key,
                "public_url": public_url
            }
        except Exception as e:
            pprint({"ERROR": f"Failed to upload photo: {str(e)}"})
            raise e

    def generate_tempo_url_url(self, s3_key: str, expires_in: int = 3600) -> str:
        try:
            url = self.s3_client.generate_presigned_url(
                ClientMethod='get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            pprint({"ERROR": f"Failed to generate tempo URL: {str(e)}"})
            raise e

    def get_file_from_s3(self, s3_key):
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=s3_key)
            file_content = response["Body"].read()

            encoded_file = base64.b64encode(file_content).decode("utf-8")
            return encoded_file

        except (BotoCoreError, NoCredentialsError) as e:
            pprint({"ERROR": "Failed to get file from S3", "reason": str(e)})
            return None
