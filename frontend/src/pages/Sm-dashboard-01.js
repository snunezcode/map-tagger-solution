import {useState,useEffect,useRef} from 'react'
import { createSearchParams } from "react-router-dom";
import Axios from 'axios'
import { configuration, SideMainLayoutHeader,SideMainLayoutMenu, breadCrumbs } from './Configs';
import { applicationVersionUpdate, getMatchesCountText, createLabelFunction, paginationLabels, pageSizePreference, collectionPreferencesProps, EmptyState, customFormatNumberShort, customFormatNumberLong, customFormatNumber } from '../components/Functions';

import { useCollection } from '@cloudscape-design/collection-hooks';
import {CollectionPreferences,Pagination } from '@cloudscape-design/components';
import TextFilter from "@cloudscape-design/components/text-filter";

import CustomHeader from "../components/Header";
import AppLayout from "@cloudscape-design/components/app-layout";
import SideNavigation from '@cloudscape-design/components/side-navigation';

import Flashbar from "@cloudscape-design/components/flashbar";
import { StatusIndicator } from '@cloudscape-design/components';
import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import Table from "@cloudscape-design/components/table";
import Header from "@cloudscape-design/components/header";
import Box from "@cloudscape-design/components/box";
import ColumnLayout from "@cloudscape-design/components/column-layout";
import Container from "@cloudscape-design/components/container";
import { SplitPanel } from '@cloudscape-design/components';

import '@aws-amplify/ui-react/styles.css';



import CustomTable02 from "../components/Table02";
import NativeChartBar01 from '../components/NativeChartBar-01';




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




//-- Encryption
var CryptoJS = require("crypto-js");

function Login() {
    
    //-- Application Messages
    const [applicationMessage, setApplicationMessage] = useState([]);
  
    //-- Variable for Split Panels
    const [splitPanelShow,setsplitPanelShow] = useState(false);
    const [selectedItems,setSelectedItems] = useState([{ identifier: "" }]);
    
    // Metrics
    const [globalMetrics, setGlobalMetrics] = useState({ 
                                                          summaryResources : { resourceTagged : [], resourceAdded : [], resourceSkipped : [] },
                                                          summaryServices : [], 
      
    });
    
    //-- Variables Table
    const columnsTableResources = [
                  {id: 'process_id',header: 'ProcessId',cell: item => item.process_id,ariaLabel: createLabelFunction('process_id'),sortingField: 'process_id',},
                  {id: 'accounts',header: 'Accounts',cell: item => item.accounts,ariaLabel: createLabelFunction('accounts'),sortingField: 'accounts',},
                  {id: 'regions',header: 'Regions',cell: item => item.regions,ariaLabel: createLabelFunction('regions'),sortingField: 'regions',},
                  {id: 'total_resources',header: 'TotalResources',cell: item => item.total_resources,ariaLabel: createLabelFunction('total_resources'),sortingField: 'total_resources',},
                  {id: 'total_resources_tagged',header: 'TotalResourcesTagged',cell: item => item.total_resources_tagged,ariaLabel: createLabelFunction('total_resources_tagged'),sortingField: 'total_resources_tagged',},
                  {id: 'total_resources_added',header: 'TotalResourcesAdded',cell: item => item.total_resources_added,ariaLabel: createLabelFunction('total_resources_added'),sortingField: 'total_resources_added',},
                  {id: 'total_resources_skipped',header: 'TotalResourcesSkipped',cell: item => item.total_resources_skipped,ariaLabel: createLabelFunction('total_resources_skipped'),sortingField: 'total_resources_skipped',},
    ];
    const visibleTableResources = ['process_id', 'regions', 'accounts',  'total_resources', 'total_resources_tagged', 'total_resources_added', 'total_resources_skipped'];
    const [itemsTableResources,setItemsTableResources] = useState([]);
    
    
    const columnsTableResourcesDetails = [
                  {id: 'id',header: 'Identifier',cell: item => item.id,ariaLabel: createLabelFunction('id'),sortingField: 'id',},
                  {id: 'process_id',header: 'ProcessId',cell: item => item.process_id,ariaLabel: createLabelFunction('process_id'),sortingField: 'process_id',},
                  {id: 'account_id',header: 'AccountId',cell: item => item.account_id,ariaLabel: createLabelFunction('account_id'),sortingField: 'account_id',},
                  {id: 'region',header: 'Region',cell: item => item.region,ariaLabel: createLabelFunction('region'),sortingField: 'region',},
                  {id: 'service',header: 'Service',cell: item => item.service,ariaLabel: createLabelFunction('service'),sortingField: 'service',},
                  {id: 'resource_name',header: 'Resource',cell: item => item.resource_name,ariaLabel: createLabelFunction('resource_name'),sortingField: 'resource_name',},
                  {id: 'creation_date',header: 'LaunchTime',cell: item => item.creation_date,ariaLabel: createLabelFunction('creation_date'),sortingField: 'creation_date',},
                  {id: 'tag_key',header: 'TagName',cell: item => item.tag_key,ariaLabel: createLabelFunction('tag_key'),sortingField: 'tag_key',},
                  {id: 'tag_value',header: 'TagValue',cell: item => item.tag_value,ariaLabel: createLabelFunction('tag_value'),sortingField: 'tag_value',},
                  {id: 'type',header: 'Type',cell: item => item.type_desc,ariaLabel: createLabelFunction('type'),sortingField: 'type',},
                  {id: 'timestamp',header: 'Timestamp',cell: item => item.timestamp,ariaLabel: createLabelFunction('timestamp'),sortingField: 'timestamp',},
    ];
    const visibleTableResourcesDetails = ['id', 'process_id', 'account_id', 'region',  'service', 'resource_name', 'creation_date', 'type'];
    const [itemsTableResourcesDetails,setItemsTableResourcesDetails] = useState([]);
    
    
    const columnsTableTags = [
                  {id: 'key',header: 'Key',cell: item => item.Key,ariaLabel: createLabelFunction('key'),sortingField: 'key', width : "250px"},
                  {id: 'value',header: 'Value',cell: item => item.Value,ariaLabel: createLabelFunction('value'),sortingField: 'value',},
    ];
    const visibleTableTags = ['key', 'value'];
    const [itemsTableTags,setItemsTableTags] = useState([]);
    
    var currentProcessId = useRef("");
    
    //-- Add Header Cognito Token
    Axios.defaults.headers.common['x-token-cognito'] = sessionStorage.getItem("x-token-cognito");
    Axios.defaults.withCredentials = true;
    
    
    //-- Handle Click Events - Tagger Process
    async function startTaggerProcess (){
            try{
            const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/process/collection/start`);
            sessionStorage.setItem("x-csrf-token", data.csrfToken );
            console.log(data);
            setApplicationMessage([
                              {
                                type: "info",
                                content: "Tagger Process has been started, click on Refresh button to update page information. ",
                                dismissible: true,
                                dismissLabel: "Dismiss message",
                                onDismiss: () => setApplicationMessage([]),
                                id: "message_1"
                              }
            ]);
        }
        catch{
          console.log('Timeout API error : /api/aws/tagger/process/collection/start');                  
        }
    };
    
    
    
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
    
    
     //-- Call API to gather process
   async function gatherTaggerProcessDetails(){
        try{
        
            var params = { process_id : currentProcessId.current };
            const { data } = await Axios.get(`${configuration["apps-settings"]["api-url"]}/api/aws/tagger/process/details`,{
                      params: params, 
            });
            sessionStorage.setItem("x-csrf-token", data.csrfToken );
            setItemsTableResourcesDetails(data.records);
            
            
        }
        catch{
          console.log('Timeout API error : /api/aws/tagger/process/details');                  
        }
    }
    
    
    
    function convertToObjects(tagListString) {
      try {
        console.log(tagListString);
        
        // Remove the outer parentheses and square brackets from the string
        var innerString = "";
        if (tagListString.substring(0,2) == "[[")
          innerString = tagListString.slice(1, -1);
        else
          innerString = tagListString;
        
        //console.log(innerString);
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

    
    
    
    
    //-- Init Function
    // eslint-disable-next-line
    useEffect(() => {
        gatherTaggerProcess();
        //const id = setInterval(gatherTablesDetails, configuration["apps-settings"]["refresh-interval-dynamodb"]);
        //return () => clearInterval(id);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);
    
    useEffect(() => {
        //gatherVersion();
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
                                     {"Resource : " + selectedItems['resource_name']}
                              </Header>
                            
                          } 
                          i18nStrings={splitPanelI18nStrings} closeBehavior="hide"
                          onSplitPanelToggle={({ detail }) => {
                                         //console.log(detail);
                                        }
                                      }
                      >
                        
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
                        
                        
                        
                            
                      </SplitPanel>
            }
            content={
                      <div style={{"padding" : "1em"}}>
                          <Flashbar items={applicationMessage} />
                          <br/>
                          <Container
                            header={
                                      <Header
                                        variant="h2"
                                        description='Summary of resources tagget'
                                        actions={
                                          <SpaceBetween
                                            direction="horizontal"
                                            size="xs"
                                          >
                                            <Button onClick={startTaggerProcess} variant={"primary"}>Launch Tagging Process</Button>
                                            <Button onClick={gatherTaggerProcess} variant={"primary"}>Refresh</Button>
                                          </SpaceBetween>
                                        }
                                      >
                                        Summay Tagging Process
                                      </Header>
                                    }
                          >
                          
                            <table style={{"width":"100%"}}>
                                <tr>  
                                    <td valign="middle" style={{"width":"50%", "padding-right": "2em", "text-align": "center"}}>  
                                          <NativeChartBar01 
                                              extendedProperties = {
                                                  { hideFilter : true } 
                                              }
                                              height={"250"}
                                              series={[
                                                        {
                                                          title: "ResourcesAdded",
                                                          type: "bar",
                                                          data: globalMetrics['summaryResources']?.['resourceAdded']
                                                        },
                                                        {
                                                          title: "ResourcesTagged",
                                                          type: "bar",
                                                          data: globalMetrics['summaryResources']?.['resourceTagged']
                                                        },
                                                        {
                                                          title: "ResourcesSkipped",
                                                          type: "bar",
                                                          data: globalMetrics['summaryResources']?.['resourceSkipped']
                                                        },
                                                      ]}
                                          />      
                                    </td>
                                    <td valign="middle" style={{"width":"50%", "padding-right": "2em", "text-align": "center"}}>  
                                          <NativeChartBar01 
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
                              title={"Tagging Process"}
                              description={""}
                              pageSize={10}
                              onSelectionItem={( item ) => {
                                  currentProcessId.current = item[0]?.["process_id"];
                                  gatherTaggerProcessDetails();
                                }
                              }
                          />
                          <br/>
                          <CustomTable02
                              columnsTable={columnsTableResourcesDetails}
                              visibleContent={visibleTableResourcesDetails}
                              dataset={itemsTableResourcesDetails}
                              title={"Resources - " + currentProcessId.current}
                              description={""}
                              pageSize={10}
                              onSelectionItem={( item ) => {
                                  setSelectedItems(item[0]);
                                  setsplitPanelShow(true);
                                  setItemsTableTags(convertToObjects(item[0]?.['tag_list']));
                                  
                                }
                              }
                          />
                  </div>
                
            }
          />
        
    </div>
  );
}

export default Login;
