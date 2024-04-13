#!/bin/bash 
id=$(date '+%H%M%S')
start_time=$(date +%s)
role_name="arn:aws:iam::039783469744:role/role-ec2-map-tagger-solution-12a2adb699e3"
echo "`date '+%H:%M:%S'` -  ## MAP Tagger Solution Solution - Role - Creating AWS Cloudformation StackID : $id "


aws cloudformation create-stack --stack-name "map-tagger-solution-role-$id" --template-body file://MAPTaggerRole.template --parameters ParameterKey=RoleARN,ParameterValue="$role_name" --region us-east-1 --capabilities CAPABILITY_NAMED_IAM
aws cloudformation wait stack-create-complete --stack-name "map-tagger-solution-role-$id" --region us-east-1


export $(aws cloudformation describe-stacks --stack-name "map-tagger-solution-role-$id" --output text --query 'Stacks[0].Outputs[].join(`=`, [join(`_`, [`CF`, `OUT`, OutputKey]), OutputValue ])' --region us-east-1)

end_time=$(date +%s)
elapsed=$(( end_time - start_time ))
eval "echo Elapsed time: $(date -ud "@$elapsed" +'$((%s/3600/24)) days %H hr %M min %S sec')"


echo -e "\n\n\n --############### Stack Deletion ###############-- \n\n"

echo "aws cloudformation delete-stack --stack-name map-tagger-solution-role-$id --region us-east-1"