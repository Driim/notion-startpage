-include .env
export

format:
	poetry run isort src tests --profile black
	poetry run black src tests --safe

lint:
	poetry run flake8 src tests

build-lambda:
	poetry build-lambda

deploy: build-lambda
	$(eval HASH := $(shell md5sum package.zip | cut -c1-8))
	aws s3 cp package.zip s3://$(S3_BUCKET)/startpage/package-$(HASH).zip
	aws cloudformation deploy \
		--template-file template.yaml \
		--stack-name startpage \
		--capabilities CAPABILITY_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
			NotionToken=$(NOTION_TOKEN) \
			PageId=$(PAGE_ID) \
			BlockId=$(BLOCK_ID) \
			City=$(CITY) \
			ICloudUsername=$(ICLOUD_USERNAME) \
			ICloudAppPassword=$(ICLOUD_APP_PASSWORD) \
			Timezone=$(TIMEZONE) \
			S3Bucket=$(S3_BUCKET) \
			S3Key=startpage/package-$(HASH).zip
