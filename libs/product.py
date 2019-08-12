import json
import os 
import copy
from libs.dbHandle import DbHandle

class Product(object):
    def __init__(self):
        self.configDir='config'
        self.prodsFile=os.path.join(self.configDir,'product.json')
        self.templates=os.path.join(self.configDir,'templates.json')
        self.products=[]

    def getProducts(self):
        temp=''
        with open(self.prodsFile,'r') as f:
            temp=json.load(f)
        if 'product' in temp:
            for item in temp['product']:
                self.products.append(item['name'])
        return self.products

    def addNewProduct(self,config):
        products=self.getProducts()
        productName=config['productName']
        productType=config['productType']
        if productName in products:
            return False, productName+' already exists'
        
        productDict={}
        with open(self.prodsFile,'r') as f:
            productDict=json.load(f)
        productDict['product'].append({'name':productName,'type':productType})
        with open(self.prodsFile,'w') as f:
            json.dump(productDict,f)
        templates={}    
        with open (self.templates,'r') as f:
            templates=json.load(f)
        definedConfig=os.path.join(self.configDir,productName+'_defined.json')
        with open(definedConfig,'w') as f:
            json.dump(templates,f)
        for testType in ['zj','jj']:
            templates={}    
            with open (self.templates,'r') as f:
                templates=json.load(f)
            userConfig=config[testType]['test-settings']

            for temperature in templates['test-settings']:
                if temperature not in userConfig:
                    continue
                for test in templates['test-settings'][temperature]:
                    if test not in userConfig[temperature]:
                        continue
                    for item in templates['test-settings'][temperature][test]:
                        if item in userConfig[temperature][test]:
                                    #print (temperature,test,item)
                            templates['test-settings'][temperature][test][item]=userConfig[temperature][test][item]
            testItems=config[testType]['test-tasks']
            print(testItems)
            print(testType)
            for temperature in templates['test-tasks']:
                if temperature not in testItems:
                    continue
                if temperature in ['normal','low','high']:
                    templates['test-tasks'][temperature]['temperature']=testItems[temperature]['temperature']
                templates['test-tasks'][temperature]['testItems']=testItems[temperature]['testItems']

            testTypeconfig=os.path.join(self.configDir,productName+'_'+testType+'.json')
            with open(testTypeconfig,'w') as f:
                json.dump(templates,f)
        return True, 'success'

    def updateProduct(self,product,testType,config):
        products=self.getProducts()
        if product not in products:
            return False, product+' not found'
        try:
            currentConfig={}
            configFile=os.path.join(self.configDir,product+'_'+testType+'.json')
            with open(configFile,'r') as f:
                currentConfig=json.load(f)
            userConfig=config['test-settings']
            print (userConfig)
            print (currentConfig['test-settings'])
            for temperature in currentConfig['test-settings']:
                if temperature not in userConfig:
                    continue
                for test in currentConfig['test-settings'][temperature]:
                    if test not in userConfig[temperature]:
                        continue
                    for item in currentConfig['test-settings'][temperature][test]:
                        if item in userConfig[temperature][test]:
                                #print (temperature,test,item)
                            currentConfig['test-settings'][temperature][test][item]=userConfig[temperature][test][item]
            testItems=config['test-tasks']
            for temperature in currentConfig['test-tasks']:
                if temperature not in testItems:
                    continue
                if temperature in ['normal','low','high']:
                    currentConfig['test-tasks'][temperature]['temperature']=testItems[temperature]['temperature']
                currentConfig['test-tasks'][temperature]['testItems']=testItems[temperature]['testItems']
            with open(configFile,'w') as f:
                json.dump(currentConfig,f)
            return True, 'success'
        except Exception as e:
            return False, e, 

        
    def getProductConfig(self,*args) :

        products=self.getProducts()
        product,testType='',''
        if len(args)>=1 and args[0]:
            product=args[0]
            if product not in products:
                return False, product+' not found'
        else:
            product=products[0]
        if len(args)>=2 and args[1] and args[1] in ['zj','jj']:
            testType=args[1]
        else:
            testType='zj'
        try: 
            currentConfig={}

            configFile=os.path.join(self.configDir,product+'_'+testType+'.json')
            with open(configFile,'r') as f:
                currentConfig=json.load(f)
            currentConfig['product']=product
            currentConfig['testType']=testType
            currentConfig['products']=products
            return True, currentConfig
        except Exception as e:
            return False, e


    

"""
pd=Product()
print(pd.getProducts())
#config={'test-settings': {'low': {'lp': {'wait': 45, 'stableFactor': 22222222, 'samples': 3600, 'duration': 60}, 'bdys': {'frequency': 1, 'samples': 3600, 'samplesPerSpeed': 10}}, 'high': {'lp': {'wait': 45, 'stableFactor': 2, 'samples': 3600, 'duration': 60}, 'bdys': {'frequency': 1, 'samples': 3600, 'samplesPerSpeed': 10}}, 'normal': {'bdys_cfx': {'powerDown': 60, 'repetition': 6}, 'lp': {'frequency': 1, 'wait': 45, 'stableFactor': 2, 'samples': 3600, 'duration': 60}, 'bdys': {'frequency': 1, 'samples': 3600, 'samplesPerSpeed': 10}, 'lp_cfx': {'powerDown': 60, 'wait': 60, 'repetition': 6, 'duration': 60}}}, 'test-tasks': {'basic': {'testItems': ['jx', 'lz', 'fbl']}, 'high': {'testItems': ['lp', 'lp_wdx', 'bdys', 'xxd'], 'temperature': 55}, 'normal': {'testItems': ['lp', 'lp_wdx', 'lp_cfx', 'bdys',
#'xxd', 'bdys_cfx'], 'temperature': 25}, 'low': {'testItems': ['lp','bdys', 'xxd'], 'temperature': -55}}}
config={'productType': 'mn', 'jj': {'test-settings': {'low': {'lp': {'wait': 45, 'stableFactor': 2, 'samples': 3600, 'duration': 60}, 'bdys': {'frequency': 1, 'samples': 3600, 'samplesPerSpeed': 10}}, 'high': {'lp': {'wait': 45, 'stableFactor': 2, 'samples': 3600, 'duration': 60}, 'bdys': {'frequency': 1, 'samples': 3600, 'samplesPerSpeed': 10}}, 'normal': {'bdys_cfx': {'powerDown': 60, 'repetition': 6}, 'lp': {'frequency': 1, 'wait': 45, 'stableFactor': 2, 'samples': 3600, 'duration': 60}, 'bdys': {'frequency': 1, 'samples': 3600, 'samplesPerSpeed': 10}, 'lp_cfx': {'powerDown': 60, 'wait': 60, 'repetition': 6, 'duration': 60}}}, 'test-tasks': {'basic': {'testItems': ['jx', 'lz', 'fbl']}, 'high': {'testItems': ['lp', 'lp_wdx', 'bdys', 'xxd'], 'temperature': 55}, 'normal': {'testItems': ['lp', 'lp_wdx', 'lp_cfx', 'bdys',
'xxd', 'bdys_cfx'], 'temperature': 25}, 'low': {'testItems': ['lp', 'lp_wdx', 'bdys', 'xxd'], 'temperature': -55}}}, 'productName': '10FC', 'zj': {'test-settings': {'low': {'lp': {'wait': 45, 'stableFactor': 2, 'samples': 3600, 'duration': 60}, 'bdys': {'frequency': 1, 'samples': 3600, 'samplesPerSpeed': 10}}, 'high': {'lp': {'wait': 45, 'stableFactor': 2, 'samples': 3600, 'duration': 60}, 'bdys': {'frequency': 1, 'samples': 3600, 'samplesPerSpeed': 10}}, 'normal': {'bdys_cfx': {'powerDown': 60, 'repetition': 6}, 'lp': {'frequency': 1, 'wait': 45, 'stableFactor': 2, 'samples': 3600, 'duration': 60}, 'bdys': {'frequency': 1, 'samples': 3600, 'samplesPerSpeed': 10}, 'lp_cfx': {'powerDown': 60, 'wait': 60, 'repetition': 6, 'duration': 60}}}, 'test-tasks': {'basic': {'testItems': ['jx', 'lz', 'fbl']}, 'high': {'testItems': ['lp', 'lp_wdx', 'bdys', 'xxd'], 'temperature': 55}, 'normal': {'testItems': ['lp', 'lp_wdx', 'lp_cfx', 'bdys', 'xxd', 'bdys_cfx'], 'temperature': 25}, 'low':
{'testItems': ['lp', 'lp_wdx', 'bdys', 'xxd'], 'temperature': -55}}}}
#pd.updateProduct('10FD','jj',config)
print (pd.addNewProduct(config))
#print (pd.getProductConfig('10FD','jj'))
"""

        


        