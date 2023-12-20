import os
import boto3
import subprocess
import re
import pyperclip


# run this script to deploy to AWS ECR

# modify these values as needed based on the AWS account, ECR repo, and desired image tag
region = "us-west-1"
ecr_url = f"096206771424.dkr.ecr.{region}.amazonaws.com"
ecr_repository_name = "zacharygeorgebaker_backend"
image_tag = "v1.0.3"

# ------------------------------------------------------------------------------------------------------------------------------------------------

# setup boto3
SESSION = boto3.Session()
ECR_CLIENT = SESSION.client('ecr')

# color terminal text utility
class bc:
    BLUE = '\033[94m'
    RED = '\033[93m'
    ENDC = '\033[0m'

# clean local docker
result = subprocess.run(["docker", "images"], capture_output=True)
result = result.stdout.decode()
lines = result.split('\n')
images = []
if len(lines) > 1:
    for line in lines[1:]:
        parse = re.search("(.+?) +?([^ ]+?) .*", line)
        if parse is not None:
            repo = parse[1]
            tag = parse[2]
            images.append(f"{repo}:{tag}")
local_docker_image = f"{ecr_repository_name}:{image_tag}"
ecr_docker_image = f"{ecr_url}/{ecr_repository_name}:{image_tag}"
for image in [local_docker_image, ecr_docker_image]:
    if image in images:
        resp = input(f"\nImage {bc.BLUE}{image}{bc.ENDC} detected locally - delete it? [y/n] ")
        if resp.lower() != 'y':
            raise AssertionError("Aborting deploy")
        resp = subprocess.run(["docker", "image", "rm", image], capture_output=True)
        if resp.returncode != 0:
            raise AssertionError(f"Command error {' '.join(resp.args)}\n{resp.stderr.decode()}")

# check ECR
resp = ECR_CLIENT.list_images(repositoryName=ecr_repository_name)
image_tags = [x['imageTag'] for x in resp.get('imageIds', [])]
if image_tag in image_tags:
    image_tags.sort()
    raise AssertionError(f"Image tag {image_tag} detected in repository. Increment the tag or remove the existing image from the repository. {image_tags}")

# get ECR token
resp = subprocess.run(["aws", "ecr", "get-login-password", "--region", region], capture_output=True)
if resp.returncode != 0:
    raise AssertionError(f"Command error {' '.join(resp.args)}\n{resp.stderr.decode()}")
ecr_token = re.search("(.*)\n$", resp.stdout.decode())[1]

# build / push
# prints commands to run in terminal and copies them to the clipboard
commands = [
    ["docker", "build", "-t", f"{ecr_repository_name}:{image_tag}", "."],
    ["docker", "login", "-u", "AWS", "-p", ecr_token, f"{ecr_url}/{ecr_repository_name}"],
    ["docker", "tag", f"{ecr_repository_name}:{image_tag}", f"{ecr_url}/{ecr_repository_name}:{image_tag}"],
    ["docker", "push", f"{ecr_url}/{ecr_repository_name}:{image_tag}"],
]
print('\nRun these commands in the terminal:\n')
copy_str = ""
for command in commands:
    cmd_str = ' '.join(command)
    cmd_str = f"{cmd_str};"
    print(cmd_str)
    copy_str += f"{cmd_str}\n"
print('')
pyperclip.copy(copy_str)
print('*** Commands copied ***\n')
