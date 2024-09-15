import {useState,useEffect,useRef} from 'react'
import Axios from 'axios'
import { configuration, SideMainLayoutHeader,SideMainLayoutMenu, breadCrumbs } from './Configs';
import {  createLabelFunction } from '../components/Functions';


import CustomHeader from "../components/Header";
import AppLayout from "@cloudscape-design/components/app-layout";
import SideNavigation from '@cloudscape-design/components/side-navigation';

import Flashbar from "@cloudscape-design/components/flashbar";
import SpaceBetween from "@cloudscape-design/components/space-between";
import Button from "@cloudscape-design/components/button";
import Header from "@cloudscape-design/components/header";
import Box from "@cloudscape-design/components/box";
import Container from "@cloudscape-design/components/container";
import FormField from "@cloudscape-design/components/form-field";
import { SplitPanel } from '@cloudscape-design/components';
import FileUpload from "@cloudscape-design/components/file-upload";
import CustomTable02 from "../components/Table02";

import typescriptHighlight from "@cloudscape-design/code-view/highlight/typescript";
import {CodeView} from "@cloudscape-design/code-view";
import Modal from "@cloudscape-design/components/modal";

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
  
    
    //-- Modal window
    const [modalUploadVisible, setModalUploadVisible] = useState(false);
    const [modalDeleteVisible, setModalDeleteVisible] = useState(false);
    
    //-- Split Panel
    const [splitPanelShow,setsplitPanelShow] = useState(false);
    const [splitPanelSize, setSplitPanelSize] = useState(700);
    
    //-- Application messages
    const [applicationMessage, setApplicationMessage] = useState([]);
    
    //-- Add header cognito token
    Axios.defaults.headers.common['x-token-cognito'] = sessionStorage.getItem("x-token-cognito");
    Axios.defaults.withCredentials = true;
    
    //-- Table plugins
    const [pluginList, setPluginList] = useState([]);
    const [pluginContent, setPluginContent] = useState("");
    var pluginName = useRef("");
    const columnsTable =  [
                  {id: 'name', header: 'Name',cell: item => item.name,ariaLabel: createLabelFunction('name'),sortingField: 'name',},
                  {id: 'date', header: 'Last update',cell: item => item.date,ariaLabel: createLabelFunction('date'),sortingField: 'date',},
                  {id: 'size', header: 'Size',cell: item => item.size,ariaLabel: createLabelFunction('size'),sortingField: 'size',}
    ];
    const visibleContent = ['name','date','size'];
    const [fileValue, setFileValue] = useState([]);
 
  
    
    //-- View plugin content
    function viewPlugin(){
        try {
        
            var api_url = configuration["apps-settings"]["api-url"];
            var params = { fileName : pluginName.current };
            Axios.get(`${api_url}/api/aws/tagger/plugin/view`,{
                      params: params, 
                  }).then((data)=>{
                    setPluginContent(data.data.fileContent);
              })
              .catch((err) => {
                  console.log('Timeout API Call : /api/aws/tagger/plugin/view' );
                  console.log(err);
              });
            
        }
        catch{
          console.log('Timeout API error : /api/aws/tagger/plugin/view');               
          
        }
  
    }
    
    
    //-- Import plugin
    function importPlugin(){
        setModalUploadVisible(true);
    }
    
    
    
    //-- Delete plugin
    function deletePlugin(){
        setModalDeleteVisible(true);
    }
  
    
    //-- Delete plugin - confirmed
    function deletePluginConfirmed(){
        try {
        
            var api_url = configuration["apps-settings"]["api-url"];
            var params = { fileName : pluginName.current };
            Axios.get(`${api_url}/api/aws/tagger/plugin/delete`,{
                      params: params, 
                  }).then((data)=>{
                    setModalDeleteVisible(false);
                    setsplitPanelShow(false);
                    getPluginList();
                    setApplicationMessage([
                                            {
                                              type: "info",
                                              content: "Plugin file has been deleted successfully.",
                                              dismissible: true,
                                              dismissLabel: "Dismiss message",
                                              onDismiss: () => setApplicationMessage([]),
                                              id: "message_1"
                                            }
                                        ]);
              })
              .catch((err) => {
                  console.log('Timeout API Call : /api/aws/tagger/plugin/delete' );
                  console.log(err);
              });
            
        }
        catch{
          console.log('Timeout API error : /api/aws/tagger/plugin/delete');               
          
        }
    }
    
    
    
    
    //-- View plugin content
    function getPluginList(){
        try {
            
            var api_url = configuration["apps-settings"]["api-url"];
            var params = { name : pluginName.current };
            Axios.get(`${api_url}/api/aws/tagger/plugin/list`,{
                      params: params, 
                  }).then((data)=>{
                    setPluginList(data.data.fileList);
              })
              .catch((err) => {
                  console.log('Timeout API Call : /api/aws/tagger/plugin/list' );
                  console.log(err);
              });
            
        }
        catch{
          console.log('Timeout API error : /api/aws/tagger/plugin/list');               
        }
    }
    
    
    //-- Load file
    const uploadFile = async () => {
          if (fileValue) {
                  try {
                        
                        Axios.defaults.headers.common['x-csrf-token'] = sessionStorage.getItem("x-csrf-token");
                        const formData = new FormData();
                        formData.append('file', fileValue[0]);
                        formData.append('fileName', fileValue[0].name);
                        pluginName.current = fileValue[0].name;
                         await Axios({ 
                                      url: `${configuration["apps-settings"]["api-url"]}/api/aws/tagger/plugin/upload`, 
                                      method: "POST", 
                                      headers: { 
                                        'content-type': 'multipart/form-data',
                                      }, 
                                      data: formData, 
                          }) 
                            .then((res) => { 
                              
                                if (res.data.result == "success"){
                                        setApplicationMessage([
                                                          {
                                                            type: "info",
                                                            content: "Plugin file has been uploaded successfully.",
                                                            dismissible: true,
                                                            dismissLabel: "Dismiss message",
                                                            onDismiss: () => setApplicationMessage([]),
                                                            id: "message_1"
                                                          }
                                        ]);
                                        setFileValue([]);
                                        
                                  } else {
                                    
                                    setApplicationMessage([
                                                          {
                                                            type: "error",
                                                            content: "Upload process has an error, verify error logs.",
                                                            dismissible: true,
                                                            dismissLabel: "Dismiss message",
                                                            onDismiss: () => setApplicationMessage([]),
                                                            id: "message_1"
                                                          }
                                        ]);
                                    
                                  }
                              
                            }) // Handle the response from backend here 
                            .catch((err) => { 
                              
                                setApplicationMessage([
                                                          {
                                                            type: "error",
                                                            content: "Upload process has an error, verify error logs.",
                                                            dismissible: true,
                                                            dismissLabel: "Dismiss message",
                                                            onDismiss: () => setApplicationMessage([]),
                                                            id: "message_1"
                                                          }
                                        ]);
                              
                            }); // Catch errors if any 
                         
                        
                        
                  } 
                  
                  catch (error) {
                    console.error(error);
                    console.log('Timeout API error : /api/aws/tagger/plugin/upload');
                  }
                  setsplitPanelShow(false);
                  setModalUploadVisible(false);
                  getPluginList();
                  
          }
    };
    
    
    //-- Init Function
    useEffect(() => {
        getPluginList();
    }, []);
    
    
  return (
    <div style={{"background-color": "#f2f3f3"}}>
        <CustomHeader/>
        <AppLayout
            headerSelector="#h"
            toolsHide
            disableContentPaddings={true}
            breadCrumbs={breadCrumbs}
            navigation={<SideNavigation items={SideMainLayoutMenu} header={SideMainLayoutHeader} activeHref={"/plugins/"} />}
            contentType="table"
            splitPanelOpen={splitPanelShow}
            onSplitPanelToggle={() => setsplitPanelShow(false)}
            onSplitPanelResize={
                                ({ detail: { size } }) => {
                                 setSplitPanelSize(size);
                            }
            }
            splitPanelSize={splitPanelSize}
            toolsHide={true}
            splitPanel={
                      <SplitPanel  
                          header={
                          
                              <Header variant="h3">
                                     {"Plugin : " + pluginName.current }
                              </Header>
                            
                          } 
                          i18nStrings={splitPanelI18nStrings} closeBehavior="hide"
                          onSplitPanelToggle={({ detail }) => {
                                         //console.log(detail);
                                        }
                                      }
                      >
                       
                      <CodeView
                            lineNumbers
                            content={pluginContent}
                            
                      /> 
                            
                      </SplitPanel>
            }
            content={
                      <div style={{"padding" : "1em"}}>
                          <Flashbar items={applicationMessage} />
                          <br/>
                          <Container
                                    header={<Header variant="h2" description="MapTagger utilizes a plugin mechanism to perform discovery and tagging processes for AWS services. You can add additional services as needed. To view the content of a specific plugin, select it from the plugin table.">
                                            {"Plugin management"}
                                          </Header>
                                      } 
                          >
                           <table style={{"width":"100%"}}>
                                <tr>  
                                    <td valign="middle" style={{"width":"100%", "padding-right": "2em", "text-align": "center"}}> 
                                    
                                    
                                        <CustomTable02
                                                columnsTable={columnsTable}
                                                visibleContent={visibleContent}
                                                dataset={pluginList}
                                                title={"Plugins"}
                                                description={""}
                                                pageSize={10}
                                                onSelectionItem={( item ) => {
                                                      pluginName.current = item[0]?.['name'];
                                                      viewPlugin();
                                                      setsplitPanelShow(true);
                                                  }
                                                }
                                                extendedTableProperties = {
                                                    { variant : "borderless" }
                                                    
                                                }
                                                tableActions = {
                                                        <SpaceBetween
                                                            direction="horizontal"
                                                            size="xs"
                                                          >
                                                          <Button variant="primary" onClick={ deletePlugin }>Delete</Button>
                                                          <Button variant="primary" onClick={ importPlugin }>Upload</Button>
                                                          <Button variant="primary" onClick={ getPluginList }>Refresh</Button>
                                                        </SpaceBetween>
                                                }
                                                
                                        />
                                    </td>
                                </tr>
                            </table>
                            
                          </Container>
                          
                          <Modal
                              onDismiss={() => { 
                                  setModalUploadVisible(false);
                              }}
                              visible={modalUploadVisible}
                              closeAriaLabel="Close modal"
                              header={
                                    <Header
                                        variant="h3"
                                    >  
                                           {"Upload plugin"}
                                    </Header> 
                                
                              }
                            >
                                  <FormField
                                            label="Select the plugin file to be imported"
                                  >
                                       
                                        <FileUpload
                                          onChange={({ detail }) => {
                                              setFileValue(detail.value);
                                              console.log(detail.value);
                                            }
                                          }
                                          value={fileValue}
                                          i18nStrings={{
                                            uploadButtonText: e =>
                                              e ? "Choose files" : "Choose file",
                                            dropzoneText: e =>
                                              e
                                                ? "Drop files to upload"
                                                : "Drop file to upload",
                                            removeFileAriaLabel: e =>
                                              `Remove file ${e + 1}`,
                                            limitShowFewer: "Show fewer files",
                                            limitShowMore: "Show more files",
                                            errorIconAriaLabel: "Error"
                                          }}
                                          showFileLastModified
                                          showFileSize
                                          showFileThumbnail
                                          tokenLimit={3}
                                          constraintText="File has to be python script file (.py)"
                                        />
                                        <br/>
                                        <Box>
                                            <SpaceBetween
                                              direction="horizontal"
                                              size="xs"
                                            >
                                              <Button onClick={uploadFile} variant={"primary"}>Upload</Button>
                                            </SpaceBetween>
                                        </Box>
                                </FormField>
                            </Modal>
                            
                            
                            <Modal
                                  onDismiss={() => setModalDeleteVisible(false)}
                                  visible={modalDeleteVisible}
                                  footer={
                                    <Box float="right">
                                      <SpaceBetween direction="horizontal" size="xs">
                                        <Button variant="primary" onClick={() => setModalDeleteVisible(false)}>Cancel</Button>
                                        <Button variant="primary" onClick={deletePluginConfirmed}>Delete</Button>
                                      </SpaceBetween>
                                    </Box>
                                  }
                                  header={"Delete plugin - " + pluginName.current}
                                >
                                  Do you want delete this plugin ?
                          </Modal>
                  </div>
                
            }
          />
        
    </div>
  );
}

export default Application;
