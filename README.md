## About Amazon Connect Users CDK
This solution can be used to create and configure users in Amazon Connect.

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
