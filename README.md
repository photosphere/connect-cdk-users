## About Amazon Connect Users CDK
This solution can be used to create and configure users in Amazon Connect.

### Requirements

1.[AWS CDK 2.100.0 installed](https://docs.aws.amazon.com/cdk/v2/guide/home.html)

2.[NodeJS 14.x installed](https://nodejs.org/en/download/)

### Installation

Clone the repo

```bash
git clone https://github.com/photosphere/connect-cdk-users.git
```

cd into the project root folder

```bash
cd connect-cdk-users
```

#### Create virtual environment

##### via python

Then you should create a virtual environment named .venv

```bash
python -m venv .venv
```

and activate the environment.

On Linux, or OsX 

```bash
source .venv/bin/activate
```
On Windows

```bash
source.bat
```

Then you should install the local requirements

```bash
pip install -r requirements.txt
```
### Build and run the Application Locally

```bash
streamlit run users/users_stack.py
```

### Or Build and run the Application on Cloud9

```bash
streamlit run users/users_stack.py --server.port 8080 --server.address=0.0.0.0 
```
#### Deployment screenshot
<img width="1573" alt="deploy_screenshot" src="https://github.com/photosphere/connect-cdk-users/assets/3398595/7da69203-7c4f-4fab-8200-eaeb58a33d27">

#### Cloudformation screenshot
<img width="1360" alt="connect-users-stack" src="https://github.com/photosphere/connect-cdk-users/assets/3398595/473c3faa-e639-438a-a252-0cfe3ceda358">

#### Configuration(ACW) screenshot
<img width="1557" alt="configure_acw_screenshot" src="https://github.com/photosphere/connect-cdk-users/assets/3398595/627b60bc-b019-4cc1-a08d-7be9910efc7f">

#### Configuration(Profile) screenshot
<img width="1557" alt="configure_profile_screenshot" src="https://github.com/photosphere/connect-cdk-users/assets/3398595/2b2cc041-cd77-4855-8ab3-24b702b0e8e4">
