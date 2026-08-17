from __future__ import annotations

import os
from pathlib import Path
from typing import BinaryIO

import boto3


class MediaStorage:
    def __init__(self, local_root: Path):
        self.local_root = local_root
        self.bucket = os.getenv("AWS_S3_BUCKET")
        self.region = os.getenv("AWS_REGION", "us-east-1")
        self.endpoint_url = os.getenv("AWS_S3_ENDPOINT_URL")
        self.public_base_url = os.getenv("AWS_S3_PUBLIC_BASE_URL")
        self.client = (
            boto3.client("s3", region_name=self.region, endpoint_url=self.endpoint_url)
            if self.bucket
            else None
        )
        self.local_root.mkdir(parents=True, exist_ok=True)

    @property
    def uses_s3(self) -> bool:
        return self.client is not None and self.bucket is not None

    def save(self, source: BinaryIO, filename: str, content_type: str) -> str:
        if self.uses_s3:
            key = f"uploads/{filename}"
            self.client.upload_fileobj(
                source,
                self.bucket,
                key,
                ExtraArgs={"ContentType": content_type},
            )
            if self.public_base_url:
                return f"{self.public_base_url.rstrip('/')}/{key}"
            return f"https://{self.bucket}.s3.{self.region}.amazonaws.com/{key}"

        destination = self.local_root / filename
        with destination.open("wb") as output:
            while chunk := source.read(1024 * 1024):
                output.write(chunk)
        return f"/media/{filename}"
