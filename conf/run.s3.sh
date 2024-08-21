#!/bin/bash 
id=$(date '+%H%M%S')
start_time=$(date +%s)

echo "`date '+%H:%M:%S'` -  ## MAP Tagger Solution Solution - Creating AWS Cloudformation StackID : $id "


aws cloudformation create-stack --stack-name "map-tagger-solution-$id" --template-body file://MAPTaggerSolution.s3.template --parameters ParameterKey=Username,ParameterValue=snmatus@amazon.com ParameterKey=VPCParam,ParameterValue=vpc-07d80a425057895a3 ParameterKey=SubnetParam,ParameterValue=subnet-03bff4b2b43b0d393 ParameterKey=InstanceType,ParameterValue=t3a.medium ParameterKey=PublicAccess,ParameterValue=true ParameterKey=SGInboundAccess,ParameterValue=0.0.0.0/0 ParameterKey=CodeRepository,ParameterValue=https://map-tagger.s3.amazonaws.com --region us-east-1 --capabilities CAPABILITY_NAMED_IAM
aws cloudformation wait stack-create-complete --stack-name "map-tagger-solution-$id" --region us-east-1


export $(aws cloudformation describe-stacks --stack-name "map-tagger-solution-$id" --output text --query 'Stacks[0].Outputs[].join(`=`, [join(`_`, [`CF`, `OUT`, OutputKey]), OutputValue ])' --region us-east-1)

end_time=$(date +%s)
elapsed=$(( end_time - start_time ))
eval "echo Elapsed time: $(date -ud "@$elapsed" +'$((%s/3600/24)) days %H hr %M min %S sec')"


echo -e "\n\n\n --############### Connection Information ###############-- \n\n"
echo " StackID  : $id"
echo " PublicAppURL   : $CF_OUT_PublicAppURL"
echo " PrivateAppURL   : $CF_OUT_PrivateAppURL"
echo " RoleARN   : $CF_OUT_RoleARN"

echo -e "\n\n\n --############### Stack Deletion ###############-- \n\n"

echo "aws cloudformation delete-stack --stack-name map-tagger-solution-$id --region us-east-1"
echo "aws cloudformation wait stack-delete-complete --stack-name map-tagger-solution-$id --region us-east-1"



