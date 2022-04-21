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
   1. 上海主城区面要素(`sh_main.shp`)
   2. 上海主城区乡镇面要素(`sh_main_town.shp`)
   3. 带有各种人口及房价信息的居民建筑物轮廓面要素(`sh_main_building.shp`)
   4. 上海主城区的lucc数据(`sh_main_lucc.shp`)
   5. 上海主城区5m乘5m蓝绿空间类型(`sh_main_green.shp`)
4. **栅格数据**
   1. 上海主城区ndvi(`rsh_main_ndvi.tif`)
   2. 上海主城区5m乘5m蓝绿空间类型(`rsh_main_green.tif`)
   3. 上海主城区居民人口密度(`rsh_main_pop.tif`)
   4. 上海主城区居民男性人口密度(`rsh_main_male.tif`)
   5. 上海主城区居民女性人口密度(`rsh_main_female.tif`)
   6. 上海主城区居民外来人口密度(`rsh_main_for.tif`)
   7. 上海主城区居民0-14岁人口密度(`rsh_main_14.tif`)
   8. 上海主城区居民15-64岁人口密度(`rsh_main_64.tif`)
   9. 上海主城区居民65岁以上人口密度(`rsh_main_65plus.tif`)
   10. 上海主城区房价(`rsh_main_price.tif`)

## 处理流程
### 1. 创建格网分析单元
   1. 市中心面(`sh_main`)转换成5m乘5m格网(`sh_main_grid`)
   2. 市中心格网(`sh_main_grid`)添加字段:`id` 作为每个格网的唯一标识
   3. 市中心格网(`sh_main_grid`)添加字段:`area` 作为每个格网的面积
   4. 市中心格网(`sh_main_grid`)转换成点(`sh_main_grid_point`) __(用于点转栅格)__
### 2. 计算每个网格的供给与需求
   1. **供给的区域是所有包含蓝绿空间的网格**
      1. 为`sh_main_grid`添加字段`is_supply`
         1. 如果`sh_main_grid`与`sh_main_green`相交,则为1,否则为0
      2. 计算每个网格包含的蓝绿空间面积
         1. 利用`sh_main_grid`算出每个网格内`rsh_main_green.tif`的面积,添加到字段`green_area`(如果出现一个网格中存在不同的蓝绿空间类型,则取面积最大的那个)
         2. 将字段`green_area`除以网格面积`area`得到字段`green_area_score`即该网格蓝绿空间的面积比重(0-1)
         3. 利用`sh_main_grid`得到每个网格内`rsh_main_green.tif`的类型,添加到字段`green_type`(如果出现一个网格中存在不同的蓝绿空间类型,则取面积最大的那个)
         4. 为`green_type`赋权重`green_type_weight`
      3. 计算每个网格中ndvi的均值
         1. 利用`sh_main_grid`算出每个网格内`rsh_main_ndvi`的平均值,添加到字段`ndvi`
      4. 计算每个需求网格获取的供给(0-1)
         1. 遍历所有需求网格,建立15分钟步行缓冲区
         
   2. **需求的区域是所有包含居民区的网格**
      1. 为`sh_main_grid`添加字段`is_demand`
         1. 如果`sh_main_grid`与`sh_main_building`相交,则为1,否则为0
      2. 计算每个网格中的人口与房价信息
         1. 利用`sh_main_grid`与`rsh_main_pop.tif`计算每个网格内的平均人口密度,将平均人口密度*网格面积,得到人口数量字段`pop`
         2. 同上,计算男性`male`,女性`female`,外来`for`,不同年龄段`14minus`, `64minus`, `65plus`的人口数量
         3. 利用`sh_main_grid`与`rsh_main_price.tif`计算每个网格内的平均房价,得到平均房价字段`price`
  
      3.  计算每个网格中的房价均值
      4.  以每个网格点为中心,绘制15分钟步行缓冲区
      5.  统计15分钟步行缓冲区内的供给总量
      6.  以该总量作为该网格点收到的供给总量
### 3. 计算供需匹配

## Arcpy 
