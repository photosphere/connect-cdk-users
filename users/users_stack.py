from aws_cdk import (
    # Duration,
    Stack,
    CfnTag
    # aws_sqs as sqs,
)
from constructs import Construct
from aws_cdk import aws_connect as connect
import os
import subprocess
import streamlit as st
import pandas as pd
import boto3
import time
from PIL import Image
import json
from datetime import datetime


connect_client = boto3.client("connect")

st.set_page_config(
    page_title="Amazon Connect Users Deployment Tool!", layout="wide")

# app title
st.header(f"Amazon Connect Users Deployment Tool!")

connect_instance_id = ''
routing_profiles = []
security_profiles = []
users = []

if os.path.exists('connect.json'):
    with open('connect.json') as f:
        connect_data = json.load(f)
        connect_instance_id = connect_data['Id']
        connect_instance_arn = connect_data['Arn']

# connect configuration
connect_instance_id = st.text_input(
    'Connect Instance Id', value=connect_instance_id)

# load env
load_button = st.button('Load Configuration')
if load_button:
    with st.spinner('Loading......'):
        # connect configuration
        res = connect_client.describe_instance(
            InstanceId=connect_instance_id)
        connect_filtered = {k: v for k, v in res['Instance'].items() if k in [
            'Id', 'Arn']}
        with open('connect.json', 'w') as f:
            json.dump(connect_filtered, f)

        # users
        res = connect_client.list_users(
            InstanceId=connect_instance_id)
        df = pd.DataFrame(res['UserSummaryList'])
        if len(df) > 0:
            df.to_csv("users_update.csv", index=False)

        # routing profiles
        res = connect_client.list_routing_profiles(
            InstanceId=connect_instance_id,)
        df = pd.DataFrame(res['RoutingProfileSummaryList'])
        if len(df) > 0:
            df.to_csv("routing_profiles.csv", index=False)

        # security profiles
        res = connect_client.list_security_profiles(
            InstanceId=connect_instance_id)
        df = pd.DataFrame(res['SecurityProfileSummaryList'])
        if len(df) > 0:
            df.to_csv("security_profiles.csv", index=False)

        st.success("Configuration loaded!")

tab1, tab2, tab3 = st.tabs(
    ["Deployment", "Configuration(ACW)", "Configuration(Profile)"])
with tab1:
    if os.path.exists('routing_profiles.csv'):
        routing_profiles = pd.read_csv("routing_profiles.csv")
        # st.write(routing_profiles)
        order_routing_profiles = routing_profiles.sort_values(
            by=["Name"], ascending=True)
        routing_profile_name_selected = st.selectbox(
            'Routing Profiles', order_routing_profiles['Name'], key=1)

    if os.path.exists('security_profiles.csv'):
        security_profiles = pd.read_csv("security_profiles.csv")
        order_security_profiles = security_profiles.sort_values(
            by=["Name"], ascending=True)
        security_profile_name_selected = st.selectbox(
            'Security Profile', order_security_profiles['Name'], key=12)

    uploaded_file = st.file_uploader(
        "Choose a CSV file of Agents", accept_multiple_files=False, type="csv", key=13)
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write(df)
        df.to_csv("agents_add.csv", index=False)


with tab2:
    if os.path.exists('users_update.csv'):
        if 'users_name_selected' not in st.session_state:
            st.session_state.users_name_selected = []

        users = pd.read_csv("users_update.csv")
        users_select_all_button = st.button('Select All Users', key=2)
        if (users_select_all_button):
            users_name_selected = st.multiselect(
                'Users', users['Username'], default=users['Username'], key=21)
        else:
            users_name_selected = st.multiselect(
                'Users', users['Username'], default=st.session_state.users_name_selected, key=22)
        users_selected = users[users['Username'].isin(users_name_selected)]
        if st.session_state.users_name_selected != users_name_selected:
            st.session_state.users_name_selected = users_name_selected

        acw_val = st.number_input(
            'After Contact Work (ACW) timeout', step=1, min_value=0)
        auto_accept_val = st.checkbox('Auto-accept calls')
        update_button = st.button('Update User Configuration', key=23)
        if (update_button):
            connect_client = boto3.client("connect")
            for index, row in users_selected.iterrows():
                res = connect_client.update_user_phone_config(
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

with tab3:
    if os.path.exists('routing_profiles.csv'):
        routing_profiles = pd.read_csv("routing_profiles.csv")
        order_routing_profiles = routing_profiles.sort_values(
            by=["Name"], ascending=True)
        routing_profile_name_selected = st.selectbox(
            'Routing Profiles', order_routing_profiles['Name'], key=3)
    if os.path.exists('users_update.csv'):
        if 'users_name_selected' not in st.session_state:
            st.session_state.users_name_selected = []

        users = pd.read_csv("users_update.csv")
        users_select_all_button = st.button('Select All Users', key=31)
        if (users_select_all_button):
            users_name_selected = st.multiselect(
                'Users', users['Username'], default=users['Username'], key=32)
        else:
            users_name_selected = st.multiselect(
                'Users', users['Username'], default=st.session_state.users_name_selected, key=33)
        users_selected = users[users['Username'].isin(users_name_selected)]
        if st.session_state.users_name_selected != users_name_selected:
            st.session_state.users_name_selected = users_name_selected

    update_button = st.button('Update User Configuration', key=34)
    if (update_button):
        connect_client = boto3.client("connect")
        routing_profile_selected = routing_profiles[routing_profiles['Name']
                                                    == routing_profile_name_selected]
        routing_profile_id = str(routing_profile_selected.iloc[0]['Id'])

        for index, row in users_selected.iterrows():
            res = connect_client.update_user_routing_profile(
                InstanceId=connect_instance_id,
                UserId=row["Id"],
                RoutingProfileId=routing_profile_id
            )

        st.success("Updated Successfully!")

with st.sidebar:

    # stack name
    users_stack_name = st.text_input('Stack Name (Required)')

    # stack description
    users_stack_description = st.text_area('Stack Description (Optional)')

    st.write('*You must click follow button to save configuration before deployment*')

    # save env
    if st.button('Save Configuration'):

        os.environ["users_stack_name"] = users_stack_name
        os.environ["users_stack_description"] = users_stack_description

        routing_profile_selected = routing_profiles[routing_profiles['Name']
                                                    == routing_profile_name_selected]
        profile_filtered = routing_profile_selected[[
            'Id', 'Arn']].to_json(orient='records', index=False)
        profile_filtered = json.loads(profile_filtered)
        with open('routing_profile_selected.json', 'w') as f:
            json.dump(profile_filtered[0], f)

        print(order_security_profiles)
        security_profile_selected = security_profiles[
            security_profiles['Name'] == security_profile_name_selected]
        profile_filtered = security_profile_selected[[
            'Id', 'Arn']].to_json(orient='records', index=False)
        profile_filtered = json.loads(profile_filtered)
        with open('security_profile_selected.json', 'w') as f:
            json.dump(profile_filtered[0], f)

        st.success("ENV has been set")

    # deploy cdk
    st.subheader('CDK Deployment', divider="rainbow")
    if st.button('Deploy CDK Stack'):
        subprocess.Popen(['cdk', 'deploy'])
        st.write('CDK stack initialized...........')
        time.sleep(5)
        with st.spinner('Deploying......'):
            cfm_client = boto3.client("cloudformation")
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

    # destroy cdk
    st.subheader('Clean Resources', divider="rainbow")
    if st.button('Destroy CDK Stack'):
        subprocess.Popen(['cdk', 'destroy', '--force'])
        st.write('Destroying CDK stack...........')
        time.sleep(5)
        with st.spinner('Destroying......'):
            cfm_client = boto3.client("cloudformation")
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
                        else:
                            continue
            except Exception as e:
                st.error('Failed')


class UsersStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # parameter
        if os.path.exists('connect.json'):
            with open('connect.json') as f:
                connect_data = json.load(f)
                connect_instance_arn = connect_data["Arn"]

        if os.path.exists('routing_profile_selected.json'):
            with open('routing_profile_selected.json') as f:
                profile_data = json.load(f)
                routing_profile_arn = profile_data["Arn"]

        if os.path.exists('security_profile_selected.json'):
            with open('security_profile_selected.json') as f:
                profile_data = json.load(f)
                security_profile_arns = profile_data["Arn"]

        now = datetime.now()
        formatted_now = now.strftime("%Y%m%d%H%M%S")

        # define agents
        # load agents
        agent_df = pd.read_csv("agents_add.csv")
        print()
        for index, row in agent_df.iterrows():
            cfn_user = connect.CfnUser(self, "CfnUser"+formatted_now+str(index),
                                       instance_arn=connect_instance_arn,
                                       phone_config=connect.CfnUser.UserPhoneConfigProperty(
                                           phone_type="SOFT_PHONE",

                                           # the properties below are optional
                                           auto_accept=False),
                                       routing_profile_arn=routing_profile_arn,
                                       security_profile_arns=[
                                           security_profile_arns],
                                       username=row["Username"],

                                       # the properties below are optional
                                       identity_info=connect.CfnUser.UserIdentityInfoProperty(
                                           email=row["Email"],
                                           first_name=row["FirstName"],
                                           last_name=row["LastName"]
            ),
                password=row["Password"]
            )
