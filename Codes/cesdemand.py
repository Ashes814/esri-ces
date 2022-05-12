# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import arcpy
from sklearn.preprocessing import MinMaxScaler  # 最大最小值标准化


class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the
        .pyt file)."""
        self.label = "测试工具箱"
        self.alias = "测试工具箱"

        # List of tool classes associated with this toolbox
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """Define the tool (tool name is the name of the class)."""
        self.label = "计算生态系统服务需求"
        self.description = "该工具通过网格化供给及需求面要素，使用人口密度与生态系统邻近分析计算居民对于生态系统服务的需求"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        param0 = arcpy.Parameter(
            displayName="需求居民区",
            name="demand_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param1 = arcpy.Parameter(
            displayName="供给生态系统",
            name="supply_features",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param2 = arcpy.Parameter(
            displayName="分析像元大小",
            name="cell_size",
            datatype="GPType",
            parameterType="Required",
            direction="Input")
        param2.value = 100

        param3 = arcpy.Parameter(
            displayName="研究区域",
            name="research_area",
            datatype="GPFeatureLayer",
            parameterType="Required",
            direction="Input")

        param4 = arcpy.Parameter(
            displayName="人口密度字段",
            name="population_density",
            datatype="Field",
            parameterType="Required",
            direction="Input")

        params = [param0, param1, param2, param3, param4]
        return params

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        return









    def execute(self, parameters, messages):
        def getAttributeTable(features, fields=None):
            """ get attribute table of features, you specify which fields you want to keep.
            Args:
                features [arcpy feature class]: features
                fields [List]: fields

            Return:
                df [pandas DataFrame]: Attribute Table
            """
            object_fields = arcpy.ListFields(features)
            fields_list = []

            # if fields are not set, get all fields (OID is excluded)
            if fields:
                fields_list = fields
            else:
                for object_field in object_fields:
                    fields_list.append(object_field.aliasName)
                fields_list = fields_list[2:]
            temp_dict = {}
            for f in fields_list:
                temp_dict[f] = []

            # get attribute with cursor
            for cur in arcpy.SearchCursor(features, fields_list):
                for f in fields_list:
                    try:
                        temp_dict[f].append(cur.getValue(f))
                    except:
                        temp_dict[f].append(np.nan)

            # turn data to a DataFrame
            df = pd.DataFrame(temp_dict)
            return df
        def getCrossTableValue(row, pop_dens, dist):
            """ get cross table and set the value to a sigle column.
            Args:
                row [pandas (apply)]
                pop_dens [str]: field name of population density
                dist [str]: distance to greenspace field name

            Return:
                df [pandas DataFrame]: Attribute Table
            """

            sep_val = [0.0005, 0.05, 0.1, 0.3, 1.0] # set break point

            if row[pop_dens] < sep_val[0] or row[dist] < sep_val[0]:#左闭右开
                return 1
            if row[pop_dens] < sep_val[1]:
                if row[dist] < sep_val[1]:
                    return 2
                if row[dist] < sep_val[2]:
                    return 3
                if row[dist] < sep_val[3]:
                    return 4
                if row[dist] <= sep_val[4]:
                    return 4
            if row[pop_dens] < sep_val[2]:
                if row[dist] < sep_val[1]:
                    return 3
                if row[dist] < sep_val[2]:
                    return 3
                if row[dist] < sep_val[3]:
                    return 4
                if row[dist] <= sep_val[4]:
                    return 5
            if row[pop_dens] < sep_val[3]:
                if row[dist] < sep_val[1]:
                    return 3
                if row[dist] < sep_val[2]:
                    return 4
                if row[dist] < sep_val[3]:
                    return 5
                if row[dist] <= sep_val[4]:
                    return 5
            if row[pop_dens] <= sep_val[4]:
                if row[dist] < sep_val[1]:
                    return 4
                if row[dist] < sep_val[2]:
                    return 5
                if row[dist] < sep_val[3]:
                    return 5
                if row[dist] <= sep_val[4]:
                    return 5
        def getDemandValue(demand_df, pop_dens, dist):
            """ get Demand Value with minmax Scaler.
            Args:
                demand_df [pandas DataFrame]: demand DataFrame
                pop_dens [str]: field name of population density
                dist [str]: distance to greenspace field name

            Return:
                 [ndarray]: Demand Values
            """
            # minmax scaler for all fields
            minmaxScaler = MinMaxScaler()
            std_demand_pop_dens = minmaxScaler.fit_transform(demand_df[pop_dens].values.reshape(-1, 1)).reshape(1, -1)[0]
            std_demand_dist = minmaxScaler.fit_transform(demand_df[dist].values.reshape(-1, 1)).reshape(1, -1)[0]

            # calculate cross tab value with getCrossTableValue
            df = pd.DataFrame({'pop_dens':std_demand_pop_dens, 'dist':std_demand_dist})
            df['demand_value'] = df.apply(getCrossTableValue, axis=1, pop_dens='pop_dens', dist='dist')
            return df['demand_value'].values

        def calDemandValue(features, pop_dens, dist):
            """ main function for calculating demand value and set it to features
            Args:
                features [arcpy features]
                pop_dens [str]: field name of population density
                dist [str]: distance to greenspace field name

            Return:
                None
            """
            attributeTable = getAttributeTable(features, fields=[pop_dens, dist])
            dv = getDemandValue(attributeTable, pop_dens, dist)

            arcpy.AddField_management(features, 'demand_value', 'SHORT')
            i = 0

            # use update Cursor to calculate
            with arcpy.da.UpdateCursor(features,['demand_value']) as cur:
                for row in cur:
                    row[0] = dv[i]
                    i += 1
                    cur.updateRow(row)
        """The source code of the tool."""
        arcpy.env.workspace = r"D:\MyDrivers\esri-ces\Codes\temp\test.gdb"
        arcpy.management.CreateFishnet(out_feature_class='grid',
                                       origin_coord='331981.0468 3428350.4767',
                                       y_axis_coord='331981.0468 3428360.4767',
                                       cell_width=parameters[2].value,
                                       cell_height=parameters[2].value,
                                       template=parameters[3].valueAsText)

        # 将位于居民区内的网格点提取出来
        arcpy.analysis.SpatialJoin(target_features='grid_label',
                                   join_features=parameters[0].valueAsText,
                                   out_feature_class='demand_point',
                                   join_type='KEEP_COMMON',
                                   match_option='WITHIN')

        # 将位于绿色空间内的网格点提取出来
        arcpy.analysis.SpatialJoin(target_features='grid_label',
                                   join_features=parameters[1].valueAsText,
                                   out_feature_class='supply_point',
                                   join_type='KEEP_COMMON',
                                   match_option='WITHIN')

        # 计算每个demand_point到最近的supply_point的距离
        arcpy.analysis.Near(in_features='demand_point',
                            near_features='supply_point')

        calDemandValue('demand_point', parameters[4].value, 'NEAR_DIST')

        arcpy.conversion.PointToRaster(in_features='demand_point',
                               value_field='demand_value',
                               out_rasterdataset='CESDemand',
                               cellsize=parameters[2].value)
        return
