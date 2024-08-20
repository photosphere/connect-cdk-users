import os
import subprocess
import json
import time
from datetime import datetime

import streamlit as st
import pandas as pd
import boto3
from aws_cdk import Stack
from aws_cdk import aws_connect as connect
from constructs import Construct

# Constants
CONFIG_FILE = 'connect.json'
USERS_FILE = 'users_update.csv'
ROUTING_PROFILES_FILE = 'routing_profiles.csv'
SECURITY_PROFILES_FILE = 'security_profiles.csv'
AGENTS_FILE = 'agents_add.csv'

# AWS clients
connect_client = boto3.client("connect")
cfm_client = boto3.client("cloudformation")

# Streamlit page configuration
st.set_page_config(
    page_title="Amazon Connect Users Deployment Tool!", layout="wide")
st.header("Amazon Connect Users Deployment Tool!")

# Helper functions


def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}


def save_json(data, filename):
    with open(filename, 'w') as f:
        json.dump(data, f)


def load_csv(filename):
    if os.path.exists(filename):
        return pd.read_csv(filename)
    return pd.DataFrame()


# Load configuration
connect_data = load_json(CONFIG_FILE)
connect_instance_id = connect_data.get('Id', '')

# Connect configuration
connect_instance_id = st.text_input(
    'Connect Instance Id', value=connect_instance_id)

# Load environment


def load_configuration():
    with st.spinner('Loading......'):
        # Connect configuration
        res = connect_client.describe_instance(InstanceId=connect_instance_id)
        connect_filtered = {k: v for k, v in res['Instance'].items() if k in [
            'Id', 'Arn']}
        save_json(connect_filtered, CONFIG_FILE)

        # Users
        res = connect_client.list_users(InstanceId=connect_instance_id)
        df = pd.DataFrame(res['UserSummaryList'])
        if not df.empty:
            df.to_csv(USERS_FILE, index=False)

        # Routing profiles
        res = connect_client.list_routing_profiles(
            InstanceId=connect_instance_id)
        df = pd.DataFrame(res['RoutingProfileSummaryList'])
        if not df.empty:
            df.to_csv(ROUTING_PROFILES_FILE, index=False)

        # Security profiles
        res = connect_client.list_security_profiles(
            InstanceId=connect_instance_id)
        df = pd.DataFrame(res['SecurityProfileSummaryList'])
        if not df.empty:
            df.to_csv(SECURITY_PROFILES_FILE, index=False)

        st.success("Configuration loaded!")


if st.button('Load Configuration'):
    load_configuration()

# Tabs
tab1, tab2, tab3 = st.tabs(
    ["Deployment", "Configuration(ACW)", "Configuration(Profile)"])

# Deployment tab
with tab1:
    routing_profiles = load_csv(ROUTING_PROFILES_FILE)
    security_profiles = load_csv(SECURITY_PROFILES_FILE)

    if not routing_profiles.empty:
        routing_profile_name_selected = st.selectbox(
            'Routing Profiles', sorted(routing_profiles['Name']), key=11)

    if not security_profiles.empty:
        security_profile_name_selected = st.selectbox(
            'Security Profile', sorted(security_profiles['Name']), key=12)

    uploaded_file = st.file_uploader(
        "Choose a CSV file of Agents", accept_multiple_files=False, type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write(df)
        df.to_csv(AGENTS_FILE, index=False)

# Configuration(ACW) tab
with tab2:
    users = load_csv(USERS_FILE)
    if not users.empty:
        users_name_selected = st.multiselect(
            'Users', sorted(users['Username']))
        users_selected = users[users['Username'].isin(users_name_selected)]

        acw_val = st.number_input(
            'After Contact Work (ACW) timeout', step=1, min_value=0)
        auto_accept_val = st.checkbox('Auto-accept calls')

        if st.button('Update User Configuration'):
            for index, row in users_selected.iterrows():
                connect_client.update_user_phone_config(
                    PhoneConfig={
                        'PhoneType': 'SOFT_PHONE',
                        'AutoAccept': auto_accept_val,
                        'AfterContactWorkTimeLimit': acw_val,
                        'DeskPhoneNumber': ''
                    },
                    UserId=row["Id"],
                    InstanceId=connect_instance_id
                )
            st.success("Updated Successfully!")

# Configuration(Profile) tab
with tab3:
    routing_profiles = load_csv(ROUTING_PROFILES_FILE)
    users = load_csv(USERS_FILE)

    if not routing_profiles.empty:
        routing_profile_name_selected = st.selectbox(
            'Routing Profiles', sorted(routing_profiles['Name']), key=31)

    if not users.empty:
        users_name_selected = st.multiselect(
            'Users', sorted(users['Username']), key=32)
        users_selected = users[users['Username'].isin(users_name_selected)]

    if st.button('Update User Configuration', key=33):
        routing_profile_selected = routing_profiles[routing_profiles['Name']
                                                    == routing_profile_name_selected]
        routing_profile_id = str(routing_profile_selected.iloc[0]['Id'])

        for index, row in users_selected.iterrows():
            connect_client.update_user_routing_profile(
                InstanceId=connect_instance_id,
                UserId=row["Id"],
                RoutingProfileId=routing_profile_id
            )

        st.success("Updated Successfully!")

# Sidebar
with st.sidebar:
    users_stack_name = st.text_input('Stack Name (Required)')
    users_stack_description = st.text_area('Stack Description (Optional)')

    if st.button('Save Configuration'):
        os.environ["users_stack_name"] = users_stack_name
        os.environ["users_stack_description"] = users_stack_description

        routing_profile_selected = routing_profiles[routing_profiles['Name']
                                                    == routing_profile_name_selected]
        security_profile_selected = security_profiles[security_profiles['Name']
                                                      == security_profile_name_selected]

        save_json(routing_profile_selected[['Id', 'Arn']].to_dict(
            'records')[0], 'routing_profile_selected.json')
        save_json(security_profile_selected[['Id', 'Arn']].to_dict(
            'records')[0], 'security_profile_selected.json')

        st.success("ENV has been set")

    st.subheader('CDK Deployment', divider="rainbow")
    if st.button('Deploy CDK Stack'):
        subprocess.Popen(['cdk', 'deploy'])
        st.write('CDK stack initialized...........')
        time.sleep(5)
        with st.spinner('Deploying......'):
            try:
                while True:
                    time.sleep(5)
                    res = cfm_client.describe_stacks()
                    stacks = [i['StackName'] for i in res['Stacks']]
                    if os.environ["users_stack_name"] in stacks:
                        res = cfm_client.describe_stacks(
                            StackName=os.environ["users_stack_name"])
                        status = res['Stacks'][0]['StackStatus']
                        if status == 'CREATE_COMPLETE':
                            st.success('Deploy complete!')
                            break
                        elif status in ['CREATE_FAILED', 'ROLLBACK_COMPLETE']:
                            st.error(
                                'Deploy failed, please check CloudFormation event for detailed messages.')
                            break
                    else:
                        continue
            except Exception as e:
                st.error('Failed')

    st.subheader('Clean Resources', divider="rainbow")
    if st.button('Destroy CDK Stack'):
        subprocess.Popen(['cdk', 'destroy', '--force'])
        st.write('Destroying CDK stack...........')
        time.sleep(5)
        with st.spinner('Destroying......'):
            try:
                while True:
                    time.sleep(5)
                    res = cfm_client.describe_stacks()
                    stacks = [i['StackName'] for i in res['Stacks']]
                    if os.environ["users_stack_name"] not in stacks:
                        st.success('Destroy complete!')
                        break
                    else:
                        res = cfm_client.describe_stacks(
                            StackName=os.environ["users_stack_name"])
                        status = res['Stacks'][0]['StackStatus']
                        if status == 'DELETE_FAILED':
                            st.error(
                                'Destroy failed, please check CloudFormation event for detailed messages.')
                            break
            except Exception as e:
                st.error('Failed')


class UsersStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        connect_data = load_json(CONFIG_FILE)
        routing_profile_data = load_json('routing_profile_selected.json')
        security_profile_data = load_json('security_profile_selected.json')

        connect_instance_arn = connect_data.get("Arn", "")
        routing_profile_arn = routing_profile_data.get("Arn", "")
        security_profile_arns = [security_profile_data.get("Arn", "")]

        agent_df = pd.read_csv(AGENTS_FILE)

        for index, row in agent_df.iterrows():
            connect.CfnUser(self, f"CfnUser{datetime.now().strftime('%Y%m%d%H%M%S')}{index}",
                            instance_arn=connect_instance_arn,
                            phone_config=connect.CfnUser.UserPhoneConfigProperty(
                                phone_type="SOFT_PHONE",
                                auto_accept=False
                            ),
                            routing_profile_arn=routing_profile_arn,
                            security_profile_arns=security_profile_arns,
                            username=row["Username"],
                            identity_info=connect.CfnUser.UserIdentityInfoProperty(
                                email=row["Email"],
                                first_name=row["FirstName"],
                                last_name=row["LastName"]
                            ),
                            password=row["Password"]
                            )
