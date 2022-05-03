# 本仓库用于2022易智瑞开发竞赛项目文档版本控制
- [项目在线文档](https://swamp-maraca-1c5.notion.site/ESRI-6c88c4d4c597494980ce11c6b599a9ab)




## 内容介绍
- `Docs`：包括竞赛过程中的文字报告，如`项目计划书`，`项目论文`等
- `References`：包括所用参考文献内容，通过notion进行[文献管理](https://swamp-maraca-1c5.notion.site/5c17b655b6a2430f8702d1dd13302f27?v=a24ed3d7d7be468581a8f53b17c56178)


## 指标选择

## 数据准备
1. **统一CRS**:`EPSG:32651`
2. **修复几何问题**:`Fix Geometery`
3. **矢量数据**
   1. 上海主城区面要素(`sh_main.shp`) ok
   2. 上海主城区乡镇面要素(`sh_main_town.shp`) ok
   3. 带有各种人口及房价信息的居民建筑物轮廓面要素(`sh_main_building_cens.shp`) ok
   4. 上海主城区的lucc水体数据(`sh_main_lucc_water.shp`) ok
   5. 上海主城区5m乘5m蓝绿空间类型(`sh_main_green.shp`) ok
4. **栅格数据**
   1. 上海主城区ndvi(`rsh_main_ndvi.tif`) ok
   2. 上海主城区5m乘5m蓝绿空间类型(`rsh_main_green_type.tif`) ok
   3. 上海主城区居民人口密度(`rsh_main_pop.tif`) ok
   4. 上海主城区居民男性人口密度(`rsh_main_male.tif`) ok
   5. 上海主城区居民女性人口密度(`rsh_main_female.tif`) ok
   6. 上海主城区居民外来人口密度(`rsh_main_for.tif`) ok 
   7. 上海主城区居民0-14岁人口密度(`rsh_main_14.tif`) ok
   8. 上海主城区居民15-64岁人口密度(`rsh_main_64.tif`) ok
   9. 上海主城区居民65岁以上人口密度(`rsh_main_65plus.tif`) ok
   10. 上海主城区房价(`rsh_main_price.tif`) ok
   11. 上海主城区蓝绿空间要素面积(`rsh_main_green_area.tif`) ok

## 处理流程
### 1. 创建格网分析单元 
   1. 市中心面(`sh_main`)转换成5m乘5m格网(`sh_main_grid`)
      1. 对`sh_main`使用`创建渔网`工具
         1.创建文件地理数据库`test.mdb` (防止渔网过大的情况超过shp容量限制)
         2. `输出要素类`:`test.mdb/sh_main_grid`
         3. `模版范围`:`sh_main_grid`
         4. `象元高度`:5
         5. `象元宽度`:5
         6. 选择输出标注点`sh_main_grid_point`
   2. `sh_main_grid_point`利用工具`按位置选择图层`提取需求区(居民区)要素,`demand_point`(有些建筑没有点, 宝山区那块没被算进去)
      1. 输入要素`sh_main_grid_point`
      2. 关系`INTERSECT`
      3. 选择要素`sh_main_building`
      4. 其余参数默认
      5. 导出选择的要素
         1. 输出名称`demand_point` (3,425,100个)
      6. 将`demand_point`与`sh_main_building_cens`进行`空间连接`提取人口相关的属性信息
         1. 目标要素:`demand_point`
         2. 连接要素:`sh_main_building_ces`
         3. 输出要素类:`demand_point_SpatialJoin`
         4. 为`demand_point_SpatialJoin`添加字段`demand_id`
            1. 计算字段`demand_id`=`OBJECTID`
   3. `sh_main_grid_point`利用工具`按位置选择图层`提取供给区(绿地)要素`supply_point`
      1. 输入要素`sh_main_grid_point`
      2. 关系`INTERSECT`
      3. 选择要素`sh_main_green`
      4. 其余参数默认
      5. 导出选择的要素
         1. 输出名称`supply_point` (2,748,225个)
      6. 将`supply_point`与`sh_main_green`进行`空间连接`提取绿地相关的属性信息
         1. 目标要素:`supply_point`
         2. 连接要素:`sh_main_green`
         3. 输出要素类:`supply_point_SpatialJoin`
         4. 为`supply_point_SpatialJoin`添加字段`demand_id`
            1. 计算字段`supply_id`=`OBJECTID`
   4. 至此,我们完成格点数据的分析准备,下一步进行需求与供给的计算
### 2. 计算每个网格的供给与需求
   1. **供给的区域是所有包含蓝绿空间的网格**
      1. 处理每个`supply_point_SpatialJoin`要素到最近水体`sh_main_lucc_water`的距离`NEAR_DIST`
         1. `邻近`
            1. 输入要素:`supply_point_SpatialJoin`
            2. 邻近要素:`sh_main_lucc_water`
            3. 搜索半径:3000m (大于需要计算的2000m)
            4. 其余默认
      2. 计算每个`supply_point_SpatialJoin`ndvi
         1. `值提取至点`
            1. 输入点要素:`supply_point_SpatialJoin`
            2. 输入栅格:`rsh_main_ndvi`
            3. 输出点要素:`Extract_supply_1`
            4. 其余参数默认
      3. 导出`Extract_supply_1`属性表`supply_point.csv`
   
      4. 供给值计算(`pandas`)
         1. 字段处理
            1. `S_CLASS`: 绿地类型标识 -> `green_code`
            2. `NAME`: 绿地类型名称 -> `green_name`
            3. `行政区`: 行政区名称 -> `district`
            4. `supply_id`: 要素唯一标识
            5. `NEAR_DIST`: 要素至水体的距离 -> `water_dist`
            6. `RASTERVALU`: NDVI -> `ndvi` (199135个缺失值,利用该绿地类型的ndvi均值进行填充)
            7. `AREA`: 绿地面积 -> `area`
         2. 数据清洗

            1. 0-1标准化`green_area`,得到`green_area_std`
            2.  0-1标准化`ndvi`,得到`ndvi_std`
            3.  处理`green_type`, 分别附上权重`green_type_weight`
            4.  `water_distance`>1000等于9999999,用logistic函数映射得到字段`water_distance_std`(0-1)
         3. `ces_supply` = (`green_area_std` + `ndvi`)*`green_type_weight` + `water_distance_std`*0.2
         
   2. **需求的区域是所有包含居民区的网格**
      1. 处理每个`demand_point_SpatialJoin`要素到最近绿地`supply_point_SpatialJoin`的距离`NEAR_DIST`
         1. `邻近`
            1. 输入要素:`demand_point_SpatialJoin`
            2. 邻近要素:`supply_point_SpatialJoin`
            3. 搜索半径:None
            4. 其余默认
      2. 导出`demand_point_SpatialJoin`属性表`demand_point.csv`
      3. 需求值计算
         1. 字段处理
            1. 
      4. 建立`cross tabulation`计算需求
         1. 计算`sh_main_grid`每个需求网格到最近的`sh_main_green`要素的距离,得到字段`ces_distance`
         2. `sh_main_grid`每个需求网格的人口密度,即字段`pop_den`
         3. 导出`sh_main_grid`属性表`sh_main_grid_attr`
         4. 在属性表中进行判断,`pop_den`,`ces_distance`分别位于哪个区间段,赋分0-5,得到字段`ces_demand_raw`
         5. 标准化`ces_demand_raw`,形成字段`ces_demand_std`
      5. 利用`ces_demand_std`输出ces demand地图

### 3. 计算供需匹配
   1. 


## Arcpy 
