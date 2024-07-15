import { useState,useEffect,useRef } from 'react'
import Axios from 'axios'
import { configuration, SideMainLayoutHeader,SideMainLayoutMenu } from './Configs';
import { useNavigate } from "react-router-dom";

import { createLabelFunction, customFormatNumberLong } from '../components/Functions';

import SideNavigation from '@cloudscape-design/components/side-navigation';
import AppLayout from '@cloudscape-design/components/app-layout';

import Flashbar from "@cloudscape-design/components/flashbar";
import Container from "@cloudscape-design/components/container";
import Select from "@cloudscape-design/components/select";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import CustomHeader from "../components/Header";
import CustomTable02 from "../components/Table02";
import Wizard from "@cloudscape-design/components/wizard";
import Link from "@cloudscape-design/components/link";
import FormField from "@cloudscape-design/components/form-field";
import Box from "@cloudscape-design/components/box";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Alert from "@cloudscape-design/components/alert";
import Checkbox from "@cloudscape-design/components/checkbox";
import ProgressBar from "@cloudscape-design/components/progress-bar";
import ButtonDropdown from "@cloudscape-design/components/button-dropdown";
import ExpandableSection from "@cloudscape-design/components/expandable-section";
import Modal from "@cloudscape-design/components/modal";

import Header from "@cloudscape-design/components/header";
import '@aws-amplify/ui-react/styles.css';

export const splitPanelI18nStrings: SplitPanelProps.I18nStrings = {
  preferencesTitle: 'Split panel preferences',
  preferencesPositionLabel: 'Split panel position',
  preferencesPositionDescription: 'Choose the default split panel position for the service.',
  preferencesPositionSide: 'Side',
  preferencesPositionBottom: 'Bottom',
  preferencesConfirm: 'Confirm',
  preferencesCancel: 'Cancel',
  closeButtonAriaLabel: 'Close panel',
  openButtonAriaLabel: 'Open panel',
  resizeHandleAriaLabel: 'Resize split panel',
};



function Application() {
  
     let navigate = useNavigate(); 
    
    //-- Application variables
    const [activeStepIndex,setActiveStepIndex] = useState(0);
    const [checked, setChecked] = useState(false);
    var currentProcessId = useRef("");
    var inventoryState = useRef("Not-Started");
    var taggingState = useRef("Not-Started");
    var resourceSelected = useRef([{ id : "" }]);
    var actionType = useRef(0);
    var currentStep = useRef(0);
    const [visible, setVisible] = useState(false);
    var currentResource = useRef({});
    
    const processState = useRef({
                                   id : 0,
                                   process_id : "" ,
                                   inventory_status : "",
                                   inventory_start_date : "",
                                   inventory_end_date : "",
                                   inventory_items_total : 0 ,
                                   inventory_items_completed : 0 ,
                                   inventory_message : "",
                                   tagging_status : "",
                                   tagging_start_date : "",
                                   tagging_end_date : "",
                                   tagging_message : "",
                                   tagging_items_total : 0,
                                   tagging_items_completed : 0,
                                });
    
    const [statusChange, setStatusChange] = useState(false);
    const [statusProcess, setStatusProcess] = useState({});
    
    //-- Add Header Cognito Token
    Axios.defaults.headers.common['x-csrf-token'] = sessionStorage.getItem("x-csrf-token");
    Axios.defaults.headers.common['x-token-cognito'] = sessionStorage.getItem("x-token-cognito");
    Axios.defaults.withCredentials = true;
    
    
    //-- Filters
    const [filterType,setFilterType] = useState({ label: "Tagged", value: 1 });
    var currentType = useRef(1);
    
    //-- Table Variables
    const columnsTable = [
                  {id: 'id',header: 'Identifier',cell: item => (<><Button variant="inline-link" onClick={() => { showTags(item); }}>{item.id}</Button></>),ariaLabel: createLabelFunction('id'),sortingField: 'id',},
                  {id: 'process_id',header: 'ProcessId',cell: item => item.process_id,ariaLabel: createLabelFunction('process_id'),sortingField: 'process_id',},
                  {id: 'account_id',header: 'Account',cell: item => item.account_id,ariaLabel: createLabelFunction('account_id'),sortingField: 'account_id',},
                  {id: 'region',header: 'Region',cell: item => item.region,ariaLabel: createLabelFunction('region'),sortingField: 'region',},
                  {id: 'service',header: 'Service',cell: item => item.service,ariaLabel: createLabelFunction('service'),sortingField: 'service',},
                  {id: 'resource_name',header: 'Name',cell: item => item.resource_name,ariaLabel: createLabelFunction('resource_name'),sortingField: 'resource_name',},
                  {id: 'identifier',header: 'ResourceId',cell: item => item.identifier,ariaLabel: createLabelFunction('identifier'),sortingField: 'identifier',},
                  {id: 'creation_date',header: 'LaunchTime',cell: item => item.creation_date,ariaLabel: createLabelFunction('creation_date'),sortingField: 'creation_date',},
                  {id: 'tag_key',header: 'TagName',cell: item => item.tag_key,ariaLabel: createLabelFunction('tag_key'),sortingField: 'tag_key',},
                  {id: 'tag_value',header: 'TagValue',cell: item => item.tag_value,ariaLabel: createLabelFunction('tag_value'),sortingField: 'tag_value',},
                  {id: 'type',header: 'State',cell: item => item.type_desc,ariaLabel: createLabelFunction('type'),sortingField: 'type',},
                  {id: 'timestamp',header: 'Timestamp',cell: item => item.timestamp,ariaLabel: createLabelFunction('timestamp'),sortingField: 'timestamp',},
    ];
    const visibleContent = ['id', 'account_id', 'region',  'service', 'resource_name', 'identifier', 'creation_date', 'type'];
    const [resources,setResources] = useState({ records : [], summary : {} });
    
    const columnsTableTags = [
                  {id: 'key',header: 'Key',cell: item => item.Key,ariaLabel: createLabelFunction('key'),sortingField: 'key', width : "250px"},
                  {id: 'value',header: 'Value',cell: item => item.Value,ariaLabel: createLabelFunction('value'),sortingField: 'value',},
    ];
    const visibleTableTags = ['key', 'value'];
    const [itemsTableTags,setItemsTableTags] = useState([]);
    
  
                                                          
  //-- Show tag values
   async function showTags(item){
        
        try{
          
            currentResource.current = item;
            setItemsTableTags(convertToObjects(item?.['tag_list']));
            setVisible(true);
            
        }
        catch(err){
          console.log('Timeout API error : /api/aws/tagger/process/details');                  
        }
    }
  
  
    //-- Function to convert to objects
    function convertToObjects(tagListString) {
      try {
        
        // Remove the outer parentheses and square brackets from the string
        var innerString = "";
        if (tagListString.substring(0,2) == "[[")
          innerString = tagListString.slice(1, -1);
        else
          innerString = tagListString;
        
        // Parse the inner string as a JSON array
        const jsonArray = JSON.parse(`${innerString}`);
        if (Array.isArray(jsonArray))
            return jsonArray;
        else
            return [];
        
        
      } catch (error) {
        console.error('Error converting string to JSON objects:', error);
        return [];
      }
    }
    
    
  //-- Get resources discovered
   async function gatherInventoryResources (){
        
        try{
          
            var params = { process_id : currentProcessId.current, type : currentType.current };
            const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/process/details`,{
                      params: params, 
            });
            sessionStorage.setItem("x-csrf-token", data.csrfToken );
            setResources({ records : data.records, summary : data.summary });
            
        }
        catch{
          console.log('Timeout API error : /api/aws/tagger/process/details');                  
        }
    }
    
    
    
    //-- Get process status
    function getProcessStatus(){
      
        if ( currentStep.current == 0 || currentStep.current == 2) {
            try {
                var api_url = configuration["apps-settings"]["api-url"];
                var params = { processId : currentProcessId.current };
                Axios.get(`${api_url}/api/aws/tagger/process/collection/progress`,{
                          params: params, 
                      }).then((data)=>{
                         processState.current = data?.data?.status;
                         setStatusProcess(data?.data?.status);
                  })
                  .catch((err) => {
                      console.log('Timeout API Call : /api/aws/tagger/process/collection/progress' );
                      console.log(err);
                  });
            }
            catch{
            
              console.log('Timeout API error : /api/aws/tagger/process/collection/progress');                  
              
            }
        }
            

    }
    
   
   //-- Start discovery process
   async function startDiscovery(){
      
        try {
            
            currentProcessId.current =  ((new Date().toISOString().replace("T",".").substring(0, 19)).replaceAll(":","")).replaceAll("-","");
            inventoryState.current = "Started";
            var params = { processType : "inventory", processId : currentProcessId.current };
            const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/process/start`,{
                      params: params, 
            });
            sessionStorage.setItem("x-csrf-token", data.csrfToken );
            processState.current = { inventoryStatus : 1, ...processState.current };
            setStatusChange(1);
            
        }
        catch{
        
          console.log('Timeout API error : /api/aws/tagger/process/start');                  
          
        }
            

    }
    
    
    //-- Start tagging process
   async function startTagging(){
      
        try {
            
            
            taggingState.current = "Started";
            var params = { processType : "tagging", processId : currentProcessId.current };
            const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/process/start`,{
                      params: params, 
            });
            sessionStorage.setItem("x-csrf-token", data.csrfToken );
            processState.current = { taggingStatus : 1, ...processState.current };
            setStatusChange(2);
            
        }
        catch{
        
          console.log('Timeout API error : /api/aws/tagger/process/start');                  
          
        }
            

    }
    
    
    //-- Update resource action
    async function updateResourceAction(){
        
        try{
          
            var params = { process_id : currentProcessId.current, id : resourceSelected.current['id'], type : actionType.current  };
            const results = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/process/resource/update`,{
                      params: params, 
            });
            
            params = { process_id : currentProcessId.current, type : currentType.current };
            const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/process/details`,{
                      params: params, 
            });
            setResources({ records : data.records, summary : data.summary });
            
        }
        catch(err){
          console.log(err);
          console.log('Timeout API error : /api/aws/tagger/process/resource/update');                  
        }
    }
  
  
    //-- Goto dashboard
    function gotoDashboard(){
        navigate('/dashboard');
    }
    
    
   
    useEffect(() => {
        const id = setInterval(getProcessStatus, configuration["apps-settings"]["refresh-interval-tagging-process"]);
        return () => clearInterval(id);
    }, []);
    
    
    
  return (
    <div>
        <CustomHeader/>
        <AppLayout
            disableContentPaddings
            toolsHide
            navigation={<SideNavigation activeHref={"/tagging/"} items={SideMainLayoutMenu} header={SideMainLayoutHeader} />}
            contentType="default"
            content={
              <div style={{"padding" : "2em"}}>
                 
                      
      
                        <Wizard
                          i18nStrings={{
                            stepNumberLabel: stepNumber =>
                              `Step ${stepNumber}`,
                            collapsedStepsLabel: (stepNumber, stepsCount) =>
                              `Step ${stepNumber} of ${stepsCount}`,
                            skipToButtonLabel: (step, stepNumber) =>
                              `Skip to ${step.title}`,
                            navigationAriaLabel: "Steps",
                            cancelButton: "Cancel",
                            previousButton: "Previous",
                            nextButton: "Next",
                            submitButton: "Close",
                            optional: "optional"
                          }}
                          onNavigate={({ detail }) => {
                            setActiveStepIndex(detail.requestedStepIndex);
                            currentStep.current = detail.requestedStepIndex;
                            if (detail.requestedStepIndex == 1)
                            {
                              gatherInventoryResources();
                            }
                            
                          }}
                          onSubmit={
                            gotoDashboard
                          }
                          onCancel={
                            gotoDashboard
                          }
                          activeStepIndex={activeStepIndex}
                          isLoadingNextStep={ ( processState.current['inventory_status'] != "Completed"  ? true : false ) }
                          steps={[
                            {
                              title: "Perform discovery process",
                              description:
                                "Discovery process will scan and discover AWS resources for accounts and regions defined on Settings module.",
                              content: (
                                <Container
                                  header={
                                    <Header variant="h2">
                                      Discovery Process
                                    </Header>
                                  }
                                >
                                
                                    <ColumnLayout columns={1}>
                                        <div>
                                            <Box variant="p">
                                              This process will scan and discover resources in your AWS accounts, once resources are discovered you can review and tag them as part of MAP Program. Wait until discover is completed, then Click Next to review the resources discovered.
                                            </Box>
                                            <br/>
                                            { ( inventoryState.current == "Not-Started"  ) &&
                                              <>
                                                <Box>
                                                  <SpaceBetween direction="horizontal" size="xs">
                                                    <Button variant="primary" onClick={startDiscovery}>
                                                      Start discovery
                                                    </Button>
                                                  </SpaceBetween>
                                                </Box>
                                                <br/>
                                              </>
                                            }
                                            
                                            { ( ( processState.current['inventory_status'] == "Started" || processState.current['inventory_status'] == "In-progress" || inventoryState.current == "Started" ? true : false ) ) &&
                                                                
                                              <Flashbar
                                                items={[
                                                  {
                                                    content: (
                                                      <>
                                                        <ProgressBar
                                                          value={ (( processState.current['inventory_items_completed'] / processState.current['inventory_items_total']) * 100) || 0 }
                                                          additionalInfo={processState.current['inventory_message']}
                                                          description={processState.current['inventory_status']}
                                                          label={"Discovery " + ( processState.current['process_id'] != "" && processState.current['process_id'] != undefined ?  " ( Process ID: " + processState.current['process_id'] + " )" : "" ) }
                                                          variant="flash"
                                                        />
                                                        
                                                        <br/>
                                                        <Link color="inverted" external href={"/logging?logid=" + currentProcessId.current + ".log" }>
                                                          View logging
                                                        </Link>
                                                      </>
          
                                                    ),
                                                    type: ( processState.current['inventory_status'] != "Completed" ? "in-progress" : "success" ),
                                                    dismissible: false,
                                                    dismissLabel: "Dismiss message",
                                                    id: "progressbar_1"
                                                  }
                                                ]}
                                                
                                              />
                                            
                                            }
                                        </div>
                                    </ColumnLayout>
                                    
                                </Container>
                              )
                            },
                            {
                              title: "Review resources",
                              description: "Review resources discovered, define which ones are part of MAP Program, this definition will be used by tagging process to tag your migrated resources with the key: map-migrated, and the value of the tag that you provided for MAP Program.",
                              content: (
                                <Container
                                     header={
                                        <Header variant="h2">
                                          {"Process ID: " + currentProcessId.current}
                                        </Header>
                                      }
                                  >
                                  <br/>
                                  <ColumnLayout columns={4} variant="text-grid">
                                    <div>
                                      <Box variant="h1">{customFormatNumberLong(resources.summary?.['total_resources'],0) || 0 }</Box>
                                      <div>Total</div>
                                    </div>
                                    <div>
                                      <Box variant="h1">{customFormatNumberLong(resources.summary?.['total_type_1'],0) || 0 }</Box>
                                      <div>Tagged</div>
                                    </div>
                                    <div>
                                      <Box variant="h1">{customFormatNumberLong(resources.summary?.['total_type_2'],0) || 0 }</Box>
                                      <div>New</div>
                                    </div>
                                    <div>
                                      <Box variant="h1">{customFormatNumberLong(resources.summary?.['total_type_3'],0) || 0 }</Box>
                                      <div>Skipped</div>
                                    </div>
                                  </ColumnLayout>
                                  <br/>
                                  <ExpandableSection defaultExpanded headerText="Filters">
                                    <div>
                                          <ColumnLayout columns={4} variant="text-grid">
                                                <FormField
                                                    label="Action"
                                                    stretch={true}
                                                  > 
                                                        <Select
                                                        selectedOption={filterType}
                                                        onChange={({ detail }) => {
                                                          setFilterType(detail.selectedOption);
                                                          currentType.current = detail.selectedOption.value;
                                                          gatherInventoryResources();
                                                        }}
                                                        options={[
                                                          { label: "Already tagged", value: 1 },
                                                          { label: "Skipped", value: 3 },
                                                          { label: "Added", value: 2 },
                                                          { label: "Removed", value: 4 }
                                                        ]}
                                                    />
                                                            
                                                </FormField>
                                          </ColumnLayout>
                                    </div>
                                  </ExpandableSection>      
                                  <br/>
                                  <hr/>
                                  <br/>
                                  <CustomTable02
                                        columnsTable={columnsTable}
                                        visibleContent={visibleContent}
                                        dataset={resources.records}
                                        title={"Resources"}
                                        description={""}
                                        pageSize={20}
                                        onSelectionItem={( item ) => {
                                          resourceSelected.current = item[0];
                                          }
                                        }
                                        extendedTableProperties = {
                                            { variant : "borderless" }
                                        }
                                        tableActions={
                                                  <SpaceBetween
                                                    direction="horizontal"
                                                    size="xs"
                                                  >
                                                    <ButtonDropdown
                                                          onItemClick={( item ) => {
                                                            actionType.current = item.detail.id;
                                                            updateResourceAction();
                                                            }
                                                          }
                                                          items={[
                                                            {
                                                              text: "Skip resource",
                                                              id: 3
                                                            },
                                                            {
                                                              text: "Add tag value",
                                                              id: 2
                                                            },
                                                            {
                                                              text: "Remove tag value",
                                                              id: 4
                                                            }
                                                          ]}
                                                          variant="primary"
                                                  >
                                                    Action
                                                  </ButtonDropdown>
                                                  
                                                  <Button variant="primary" 
                                                          onClick={() => {
                                                              gatherInventoryResources();
                                                            }
                                                          }
                                                  >
                                                    Refresh 
                                                  </Button>
                                                  </SpaceBetween>
                                      }
                                />
                                </Container>
                              )
                            },
                            {
                              title: "Launch tagging process",
                              content: (
                                <Container
                                  header={
                                        <Header variant="h2">
                                          {"Process ID: " + currentProcessId.current}
                                        </Header>
                                      }
                                >
                                  <Alert
                                          statusIconAriaLabel="Info"
                                          header="The following resource(s) will be tagged as part MAP Program"
                                        >
                                          <br/>
                                          The use of MAP Tagger does not alter the terms of the Migration Acceleration Program (MAP) previously agreed and signed by the customer and AWS. By utilizing MAP Tagger, the user agrees to adhere to proper usage guidelines and acknowledges that any misuse is solely their responsibility. Any misuse may result in consequences including cancellation of current engagement.
                                          <br/>
                                          <br/>
                                          Migration Acceleration Program (MAP) and MAP Tagger should only be used for previously stipulated migration and/or modernization workloads.
                                          <br/>
                                          <br/>
                                          If you are unsure about the MAP terms signed please reach out to your AWS Account Team before proceeding.
                                          <br/>
                                          <br/>
                                          <Checkbox
                                              onChange={({ detail }) =>
                                                setChecked(detail.checked)
                                              }
                                              checked={checked}
                                              disabled={( taggingState.current == "Not-Started" ? false : true )}
                                            >
                                              I acknowledge that AWS resources selected are part of MAP Program.
                                            </Checkbox>
                                            
                                  </Alert>
                                  <br/>
                                  { ( taggingState.current == "Not-Started"  ) &&
                                              <>
                                                <Box>
                                                  <SpaceBetween direction="horizontal" size="xs">
                                                    <Button variant="primary" onClick={startTagging} disabled={!checked}>
                                                      Start tagging
                                                    </Button>
                                                  </SpaceBetween>
                                                </Box>
                                                <br/>
                                              </>
                                  }
                                            
                                  { ( ( processState.current['tagging_status'] == "Started" || processState.current['tagging_status'] == "In-progress" || taggingState.current == "Started" ? true : false ) ) &&
                                                      
                                    <Flashbar
                                      items={[
                                        {
                                          content: (
                                            <>
                                              <ProgressBar
                                                value={ (( processState.current['tagging_items_completed'] / processState.current['tagging_items_total']) * 100) || 0 }
                                                additionalInfo={processState.current['tagging_message']}
                                                description={processState.current['tagging_status']}
                                                label={"Tagging " + ( processState.current['process_id'] != "" && processState.current['process_id'] != undefined ?  " ( Process Identifier : " + processState.current['process_id'] + " )" : "" ) }
                                                variant="flash"
                                              />
                                              
                                              <br/>
                                              <Link color="inverted" external href={"/logging?logid=" + currentProcessId.current + ".log" }>
                                                View logging
                                              </Link>
                                            </>
                                          ),
                                          type: ( processState.current['tagging_status'] != "Completed" ? "in-progress" : "success" ),
                                          dismissible: false,
                                          dismissLabel: "Dismiss message",
                                          id: "progressbar_2"
                                        }
                                      ]}
                                      
                                    />
                                    
                                  }
                                        
                                </Container>
                              )
                            }
                          ]}
                        />
  
                
                </div>
            
            }
            
        />
        
        <Modal
            onDismiss={() => setVisible(false)}
            visible={visible}
            size={"large"}
            footer={
              <Box float="right">
                <SpaceBetween direction="horizontal" size="xs">
                  <Button variant="primary" onClick={() => setVisible(false)} >Close</Button>
                </SpaceBetween>
              </Box>
            }
            header={"Resource Identifier: " + String(currentResource.current.id)}
          >
            <br/>
            <ColumnLayout columns={4} variant="text-grid">
              <div>
                <Box variant="awsui-key-label">Resource Identifier</Box>
                <div>{currentResource.current?.['identifier']}</div>
              </div>
              <div>
                <Box variant="awsui-key-label">Account</Box>
                <div>{currentResource.current?.['account_id']}</div>
              </div>
              <div>
                <Box variant="awsui-key-label">Region</Box>
                <div>{currentResource.current?.['region']}</div>
              </div>
              <div>
                <Box variant="awsui-key-label">State</Box>
                <div>{currentResource.current?.['type_desc']}</div>
              </div>
            </ColumnLayout>
            <br/>
            <br/>
            <CustomTable02
                  columnsTable={columnsTableTags}
                  visibleContent={visibleTableTags}
                  dataset={itemsTableTags}
                  title={"Tags"}
                  description={""}
                  pageSize={10}
                  onSelectionItem={( item ) => {
                      
                    }
                  }
                  extendedTableProperties = {
                      { variant : "borderless" }
                  }
              />
          </Modal>
          
                      
    </div>
  );
}

export default Application;

