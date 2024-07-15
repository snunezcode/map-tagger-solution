import {useState,useEffect,useRef} from 'react'
import Axios from 'axios'
import { configuration, SideMainLayoutHeader,SideMainLayoutMenu, breadCrumbs } from './Configs';
import {  createLabelFunction, customFormatNumberShort } from '../components/Functions';

import CustomHeader from "../components/Header";
import AppLayout from "@cloudscape-design/components/app-layout";
import SideNavigation from '@cloudscape-design/components/side-navigation';

import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import Header from "@cloudscape-design/components/header";
import Box from "@cloudscape-design/components/box";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Container from "@cloudscape-design/components/container";
import { SplitPanel } from '@cloudscape-design/components';
import Tabs from "@cloudscape-design/components/tabs";
import Select from "@cloudscape-design/components/select";
import Modal from "@cloudscape-design/components/modal";
import CustomTable02 from "../components/Table02";
import NativeChartBar01 from '../components/NativeChartBar-01';

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
    
    
    //-- Variable for split panels
    const [splitPanelShow,setsplitPanelShow] = useState(false);
    
    // Metrics
    const [globalMetrics, setGlobalMetrics] = useState({ 
                                                          summaryResources : { resourceTagged : [], resourceAdded : [], resourceSkipped : [], resourceRemoved : [] },
                                                          summaryServices : [], 
      
    });
    
    //-- Variables table
    const columnsTableResources = [
                  {id: 'process_id',header: 'ProcessId',cell: item => item.process_id,ariaLabel: createLabelFunction('process_id'),sortingField: 'process_id',},
                  {id: 'inventory_start_date',header: 'Inventory Start',cell: item => item.inventory_start_date,ariaLabel: createLabelFunction('inventory_start_date'),sortingField: 'inventory_start_date',},
                  {id: 'inventory_end_date',header: 'Inventory End',cell: item => item.inventory_end_date,ariaLabel: createLabelFunction('inventory_end_date'),sortingField: 'inventory_end_date',},
                  {id: 'tagging_start_date',header: 'Tagging Start',cell: item => item.tagging_start_date,ariaLabel: createLabelFunction('tagging_start_date'),sortingField: 'tagging_start_date',},
                  {id: 'tagging_end_date',header: 'Tagging End',cell: item => item.tagging_end_date,ariaLabel: createLabelFunction('tagging_end_date'),sortingField: 'tagging_end_date',},
                  {id: 'total_resources',header: 'TotalResources',cell: item => item.total_resources,ariaLabel: createLabelFunction('total_resources'),sortingField: 'total_resources',},
                  {id: 'total_resources_tagged',header: 'Already Tagged',cell: item => customFormatNumberShort(item.total_resources_tagged,0),ariaLabel: createLabelFunction('total_resources_tagged'),sortingField: 'total_resources_tagged',},
                  {id: 'total_resources_skipped',header: 'Skipped',cell: item => customFormatNumberShort(item.total_resources_skipped,0),ariaLabel: createLabelFunction('total_resources_skipped'),sortingField: 'total_resources_skipped',},
                  {id: 'total_resources_added',header: 'Added',cell: item => customFormatNumberShort(item.total_resources_added,0),ariaLabel: createLabelFunction('total_resources_added'),sortingField: 'total_resources_added',},
                  {id: 'total_resources_removed',header: 'Removed',cell: item => customFormatNumberShort(item.total_resources_removed,0),ariaLabel: createLabelFunction('total_resources_removed'),sortingField: 'total_resources_removed',},    ];

    const visibleTableResources = ['process_id', 'inventory_start_date','tagging_end_date', 'total_resources', 'total_resources_tagged', 'total_resources_added', 'total_resources_skipped', 'total_resources_removed'];
    const [itemsTableResources,setItemsTableResources] = useState([]);
    
    
    const columnsTableResourcesDetails = [
                  {id: 'id',header: 'Identifier',cell: item => (<><Button variant="inline-link" onClick={() => { showTags(item); }}>{item.id}</Button></>),ariaLabel: createLabelFunction('id'),sortingField: 'id',},
                  {id: 'process_id',header: 'ProcessId',cell: item => item.process_id,ariaLabel: createLabelFunction('process_id'),sortingField: 'process_id',},
                  {id: 'account_id',header: 'AccountId',cell: item => item.account_id,ariaLabel: createLabelFunction('account_id'),sortingField: 'account_id',},
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
    const visibleTableResourcesDetails = ['id', 'account_id', 'region',  'service', 'resource_name', 'identifier', 'creation_date', 'type'];
    const [itemsTableResourcesDetails,setItemsTableResourcesDetails] = useState({ records : [], summary : {} });
    
    
    
    const columnsTableTags = [
                  {id: 'key',header: 'Key',cell: item => item.Key,ariaLabel: createLabelFunction('key'),sortingField: 'key', width : "250px"},
                  {id: 'value',header: 'Value',cell: item => item.Value,ariaLabel: createLabelFunction('value'),sortingField: 'value',},
    ];
    const visibleTableTags = ['key', 'value'];
    const [itemsTableTags,setItemsTableTags] = useState([]);
    
    
    //-- Current process selected
    var currentProcess = useRef({});
    const [visible, setVisible] = useState(false);
    var currentResource = useRef({});
    
    
    //-- Add header cognito token
    Axios.defaults.headers.common['x-token-cognito'] = sessionStorage.getItem("x-token-cognito");
    Axios.defaults.withCredentials = true;
    
    
    //-- Filters
    const [filterType,setFilterType] = useState({ label: "Tagged", value: 1 });
    var currentType = useRef(1);
    
    
    
    //-- Call API to gather process
    async function gatherTaggerProcess (){
        
        try{
        
            const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/process/list`);
            sessionStorage.setItem("x-csrf-token", data.csrfToken );
            setItemsTableResources(data.records);
            setGlobalMetrics({ summaryResources : data.summaryResources, summaryServices : data.summaryServices });
            setItemsTableResourcesDetails([]);
            
        }
        catch{
          console.log('Timeout API error : /api/aws/tagger/process/list');                  
        }
    }
    
    

    
      
  ///-- Call API to gather process details
   async function gatherTaggerProcessDetails(){
        
        try{
          
            var params = { process_id : currentProcess.current?.['process_id'] , type : currentType.current };
            const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/process/details`,{
                      params: params, 
            });
            
            setItemsTableResourcesDetails(data.records);
            
        }
        catch{
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

    
    
    
    //-- Function to Convert to CSV
    const convertToCSV = (objArray) => {
              const array = typeof objArray !== 'object' ? JSON.parse(objArray) : objArray;
              let str = '';
          
              for (let i = 0; i < array.length; i++) {
                let line = '';
                for (let index in array[i]) {
                  if (line !== '') line += ',';
          
                  line += array[i][index];
                }
                str += line + '\r\n';
              }
              return str;
    };



    //-- Function to export table to CSV
    const exportDataToCsv = (data,fileName) => {
            const csvData = new Blob([convertToCSV(data)], { type: 'text/csv' });
            const csvURL = URL.createObjectURL(csvData);
            const link = document.createElement('a');
            link.href = csvURL;
            link.download = `${fileName}.csv`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
    };
  
    
    
    
    
    //-- Show tags for especifig resource
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
    
    
    
    
    //-- Init Function
    // eslint-disable-next-line
    useEffect(() => {
        gatherTaggerProcess();
        //const id = setInterval(gatherTablesDetails, configuration["apps-settings"]["refresh-interval-dynamodb"]);
        //return () => clearInterval(id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    
   
    
  return (
    <div style={{"background-color": "#f2f3f3"}}>
        <CustomHeader/>
        <AppLayout
            headerSelector="#h"
            toolsHide
            disableContentPaddings={true}
            breadCrumbs={breadCrumbs}
            navigation={<SideNavigation items={SideMainLayoutMenu} header={SideMainLayoutHeader} activeHref={"/dashboard/"} />}
            contentType="table"
            splitPanelOpen={splitPanelShow}
            onSplitPanelToggle={() => setsplitPanelShow(false)}
            splitPanelSize={350}
            toolsHide={true}
            splitPanel={
                      <SplitPanel  
                          header={
                          
                              <Header variant="h3">
                                     {"Process Identifier : " + currentProcess.current?.['process_id']}
                              </Header>
                            
                          } 
                          i18nStrings={splitPanelI18nStrings} closeBehavior="hide"
                          onSplitPanelToggle={({ detail }) => {
                                         //console.log(detail);
                                        }
                                      }
                      >
                        <Tabs
                            tabs={[
                              {
                                label: "General information",
                                id: "first",
                                content: 
                                        <div>
                                          <ColumnLayout columns={4} variant="text-grid">
                                            <div>
                                              <Box variant="awsui-key-label">Inventory Start</Box>
                                              <div>{currentProcess.current?.['inventory_start_date']}</div>
                                            </div>
                                            <div>
                                              <Box variant="awsui-key-label">Inventory End</Box>
                                              <div>{currentProcess.current?.['inventory_end_date']}</div>
                                            </div>
                                            <div>
                                              <Box variant="awsui-key-label">Tagging Start</Box>
                                              <div>{currentProcess.current?.['tagging_start_date']}</div>
                                            </div>
                                            <div>
                                              <Box variant="awsui-key-label">Tagging End</Box>
                                              <div>{currentProcess.current?.['tagging_end_date']}</div>
                                            </div>
                                            
                                            <div>
                                              <Box variant="awsui-key-label">Resources already tagged</Box>
                                              <div>{currentProcess.current?.['total_resources_tagged']}</div>
                                            </div>
                                            <div>
                                              <Box variant="awsui-key-label">Resources added</Box>
                                              <div>{currentProcess.current?.['total_resources_added']}</div>
                                            </div>
                                            <div>
                                              <Box variant="awsui-key-label">Resources skipped</Box>
                                              <div>{currentProcess.current?.['total_resources_skipped']}</div>
                                            </div>
                                            <div>
                                              <Box variant="awsui-key-label">Resources removed</Box>
                                              <div>{currentProcess.current?.['total_resources_removed']}</div>
                                            </div>
                                          </ColumnLayout>
                                          <br/>
                                          <Box variant="awsui-key-label">Configuration</Box>
                                          <div>{currentProcess.current?.['configuration']}</div>
                                      </div>
                              },
                              {
                                label: "Resources",
                                id: "second",
                                content: 
                                        <div>  
                                            <CustomTable02
                                              columnsTable={columnsTableResourcesDetails}
                                              visibleContent={visibleTableResourcesDetails}
                                              dataset={itemsTableResourcesDetails}
                                              title={"Resources"}
                                              pageSize={10}
                                              onSelectionItem={( item ) => {
                                                  
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
                                                          <Select
                                                            selectedOption={filterType}
                                                            onChange={({ detail }) => {
                                                              setFilterType(detail.selectedOption);
                                                              currentType.current = detail.selectedOption.value;
                                                              gatherTaggerProcessDetails();
                                                            }}
                                                            options={[
                                                              { label: "Already tagged", value: 1 },
                                                              { label: "Skipped", value: 3 },
                                                              { label: "Added", value: 2 },
                                                              { label: "Removed", value: 4 }
                                                            ]}
                                                          />
                                                          <Button variant="primary" 
                                                                  onClick={() => {
                                                                    exportDataToCsv(itemsTableResourcesDetails,"test");
                                                                    }
                                                                  }
                                                          >
                                                            Export Resources 
                                                          </Button>
                                                        </SpaceBetween>
                                            }
                                            />
                                        </div>
                              }
                            ]}
                          />
                            
                      </SplitPanel>
            }
            content={
                      <div style={{"padding" : "1em"}}>
                          <br/>
                          <Container
                            header={
                                      <Header
                                        variant="h2"
                                        actions={
                                          <SpaceBetween
                                            direction="horizontal"
                                            size="xs"
                                          >
                                            <Button variant={"primary"} href="/tagging/"
                                            >
                                              Launch Tagging Process
                                            </Button>
                                            <Button onClick={gatherTaggerProcess} variant={"primary"}>Refresh</Button>
                                          </SpaceBetween>
                                        }
                                      >
                                        Tagging Execution Summary
                                      </Header>
                                    }
                          >
                          
                            <table style={{"width":"100%"}}>
                                <tr>  
                                    <td valign="middle" style={{"width":"50%", "padding-right": "2em", "text-align": "center"}}>  
                                          <NativeChartBar01 
                                              title={"Total resources by tag action"}
                                              extendedProperties = {
                                                  { hideFilter : true } 
                                              }
                                              height={"250"}
                                              series={[
                                                        {
                                                          title: "Added",
                                                          type: "bar",
                                                          data: globalMetrics['summaryResources']?.['resourceAdded']
                                                        },
                                                        {
                                                          title: "Already tagged",
                                                          type: "bar",
                                                          data: globalMetrics['summaryResources']?.['resourceTagged']
                                                        },
                                                        {
                                                          title: "Skipped",
                                                          type: "bar",
                                                          data: globalMetrics['summaryResources']?.['resourceSkipped']
                                                        },
                                                        {
                                                          title: "Removed",
                                                          type: "bar",
                                                          data: globalMetrics['summaryResources']?.['resourceRemoved']
                                                        },
                                                      ]}
                                          />      
                                    </td>
                                    <td valign="middle" style={{"width":"50%", "padding-right": "2em", "text-align": "center"}}>  
                                          <NativeChartBar01 
                                              title={"Total resources by service type"}
                                              extendedProperties = {
                                                  { hideFilter : true } 
                                              }
                                              height={"250"}
                                              series={globalMetrics['summaryServices']}
                                          />
                                    </td>
                                </tr>
                            </table>
                          </Container>
                          <br/>
                          <CustomTable02
                              columnsTable={columnsTableResources}
                              visibleContent={visibleTableResources}
                              dataset={itemsTableResources}
                              title={"Tagging Processes"}
                              description={""}
                              pageSize={10}
                              onSelectionItem={( item ) => {
                                  currentProcess.current = item[0];
                                  setsplitPanelShow(true);
                                  gatherTaggerProcessDetails();
                                }
                              }
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
