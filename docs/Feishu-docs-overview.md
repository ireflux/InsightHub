# 文档概述

本文档介绍飞书开放平台云文档中的文档能力相关的基本概念、使用限制、接入流程、方法列表等。
本文档是针对新版文档能力的说明。要了解新旧版本文档能力的区别，参考[新旧版本说明](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/docs/upgraded-docs-access-guide/upgraded-docs-openapi-access-guide)。

## 基础概念

文档 OpenAPI 中，两个基础概念为文档和块。

### 文档

文档是用户在云文档中创建的一篇在线文档。每篇文档都有唯一的 `document_id` 作为标识。要获取文档的 `document_id`，参考以下步骤。

- 若文档资源存储在云盘中，其云文档类型为文档（docx）。在该情况下，你可通过以下两种方式获取：

- 通过 URL 地址获取：直接在浏览器中打开文档，在地址栏中获取文档的 `document_id`。

![](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/f8dac29d8ea3f01f5a651e0445193213_W0CZqRcbHM.png?height=639&lazyload=true&width=2161)

- 通过开放平台接口获取

1. 通过[获取我的空间（root folder）元数据](https://open.feishu.cn/document/ukTMukTMukTM/ugTNzUjL4UzM14CO1MTN/get-root-folder-meta)获取根文件夹 token。
      2. 通过[获取文件夹下文件清单](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/file/list) 获取其中文档资源的 `document_id`。

- 若文档挂载在知识库中，你需通过知识库相关接口[获取知识空间节点信息](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/get_node)获取该节点下挂载的云资源的 `obj_token` 和 `obj_type`。在该情况下，`obj_type` 为 `docx` 时，其对应的 `obj_token`  即为文档的 `document_id`。

文档的基础元数据结构如下：

```JSON
"document": {
    "document_id": string, // 文档的唯一标识
    "revision_id": int,   // 文档版本的标识，可指定要查询或更新的文档版本
    "title": string, // 文档标题
    "display_setting": { // 文档展示设置
        "show_authors": boolean, // 文档信息中是否展示文档作者
        "show_comment_count": boolean, // 文档信息中是否展示评论总数
        "show_create_time": boolean, // 文档信息中是否展示文档创建时间
        "show_like_count": boolean, // 文档信息中是否展示点赞总数
        "show_pv": boolean, // 	文档信息中是否展示文档访问次数
        "show_uv": boolean  // 文档信息中是否展示文档访问人数
    },
    "cover": {  // 文档封面
        "token": string, // 封面图片的 token
        "offset_ratio_x": float, // 视图在水平方向的偏移比例
        "offset_ratio_y": float // 视图在垂直方向的偏移比例
    }
}
```
### 块
在一篇文档中，有多个不同类型的段落，这些段落被定义为块（Block）。块是文档中的最小构建单元，是内容的结构化组成元素，有着明确的含义。块有多种形态，可以是一段文字、一张电子表格、一张图片或一个多维表格等。每个块都有唯一的 `block_id` 作为标识。

每一篇文档都有一个根块，即页面块（Page block）。页面块的 `block_id` 与其所在文档的 `document_id` 相同。在数据结构中，文档的页面块与其它块形成父子关系，页面块为父块，称为 Parent，其它块为子块，称为 Children。其它块之间也可形成父子关系。

![](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/3afeecbc5410c1d3a9e89a2a86d89d65_VIM5eQY6T8.png?height=1721&lazyload=true&width=3059)

![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/744512f0ae06add904ef1b5625ea117b_RRPMtAFaWm.png?height=548&lazyload=true&width=1349)

**块的类别**

从功能角度，块可以分为以下几种类别。了解块的具体类型，参考 [BlockType 的枚举值](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/data-structure/block#e8ce4e8e)。

**功能类别** | <b>典型块 | <b>示例
---|---|---
文本类 | 页面（Page）、文本（Text）、标题（Heading）、无序列表（Bullet）、有序列表（Ordered）、代码（Code）、待办事项（Todo）块等。 | &nbsp;
数据类 | 多维表格（Bitable）、电子表格（Sheet）、思维笔记（Mindnote）块。 | &nbsp;
视觉类 | 分割线（Divider）块。 | &nbsp;
媒体类 | 图片（Image）、文件（File）、内嵌（Iframe）块等。 | &nbsp;
协作类 | 会话卡片（ChatCard）块。 | &nbsp;
容器类 | 表格单元格（TableCell）、分栏列（GridColumn）、高亮（Callout）、视图（View）、引用容器（QuoteContainer）块等。 | &nbsp;
垂直类 | 流程图 & UML 图（Diagram）块。 | &nbsp;
辅助类 | 表格（Table）、分栏（Grid）块等。 | &nbsp;
第三方块 | 开放平台小组件（ISV）块。 | &nbsp;
未定义块 | / | &nbsp;

**块的父子关系规则**

块与块之间可形成父子关系。在调用[创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create)接口时，你需先了解以下规则，再指定父块和子块。

**父块规则**

只有具有容纳能力的块才可以作为父块，对其添加子块。这些块包括：

- 文本功能类的块：页面（Page）、文本（Text）、标题（Heading）、无序列表（Bullet）、有序列表（Ordered）、任务（Task）、待办事项（Todo）块。
- 容器功能类的块：表格单元格（TableCell）、分栏列（GridColumn）、高亮（Callout）、引用容器（QuoteContainer）块。

**子块规则**

以下块不可作为子块被添加至父块内：

| **块**              | **说明**   |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 页面（Page）           | 一篇文档有且只有一个页面块，在文档创建时自动生成。                                                                                                                                                                                                                                             |
| 分栏列（GridColumn）    | 只可通过[更新块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/patch)接口中的 `InsertGridColumnRequest` 操作添加，不可直接作为子块添加。                                                                                                                      |
| 思维笔记（Mindnote）     | 不支持。                                                                                                                                                                                                                                                                  |
| 单元格（TableCell）     | 只可通过[更新块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/patch)接口中的 `InsertTableRowRequest` 或 `InsertTableColumnRequest` 操作添加，不可直接作为子块添加。 |
| 视图（View）           | 在添加文件（File）块时，会自动生成默认的视图块。                                                                                                                                                                                                                                            |
| 未定义（Undefined）     | 无效操作。                                                                                                                                                                                                                                                                 |
| 流程图 & UML（Diagram） | 不支持。                                                                                                                                                                                                                                                                  |
**父子关系限制**

其它的父子关系限制如下表所示：

<b>块 | <b>限制
---|---
单元格（Table Cell） | 不允许为单元格（TableCell）块添加如下块作为子块：<br>• 表格（Table）<br>• 电子表格（Sheet）<br>• 多维表格（Bitable）<br>• OKR
分栏列（Grid Column） | 不允许为分栏列（GridColumn）添加如下块作为子块：<br>• 分栏（Grid）<br>• 多维表格（Bitable）<br>• OKR
高亮块（Callout） | 只允许为高亮块（Callout）添加如下块作为子块：<br>• 文本（Text）<br>• 标题（HeadingN）<br>• 有序列表（Ordered）<br>• 无序列表（Bullet）<br>• 任务（Task）<br>• 待办事项（Todo）<br>• 引用（Quote）<br>• 引用容器（QuoteContainer）

## 使用限制

你可使用开放平台提供的一系列文档开放接口对不同种类的块进行操作，包括创建、读取、以及编辑块的内容。针对不同块，文档开放接口的支持情况不同，详情参考下表。

下表中，“/” 代表对应的操作无需支持或已在其他开放能力的场景中覆盖，具体情况如下：

- 能力无需支持。例如，分割线（Divider）块不含内容，因此开放平台无需提供读取和编辑其内容的能力；
- 能力已间接支持。例如，针对单元格（TableCell）块，你会在编辑表格（Table）块的内容时直接创建或删除单元格块，因此开放平台无需为单元格（TableCell）块单独提供创建能力；
- 能力已在其他开放能力的场景中覆盖。针对多维表格（Bitable）块，你可在创建空的多维表格块后，根据返回的 Token 值使用多维表格的开放能力调用对应的读取和编辑接口。了解多维表格的开放能力，参考[多维表格方法列表](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/bitable-overview)。

| **块** | **创建块** | **读取内容** | **编辑内容** |
  |---|---|---|---|
  | 高亮块（Callout） | 支持 | 支持 | 支持 |
  | 表格（Table） | 支持 | 支持 | 支持 |
  | 文本（Text） | 支持 | 支持 | 支持 |
  | 分割线（Divider） | 支持 | / | / |
  | 分栏（Grid） | 支持 | 支持 | 支持 |
  | 内嵌块（Iframe） | 支持 | 支持 | 不支持 |
  | 会话卡片（ChatCard） | 支持 | / | / |
  | 图片（Image） | 支持 | / | / |
  | 文件（File） | 支持 | / | / |
  | 单元格（TableCell） | / | 支持 | 支持 |
  | 分栏列（GridColumn） | / | 支持 | 支持 |
  | 视图（View） | / | 支持 | 不支持 |
  | 三方块（ISV） | 支持 | / | / |
  | 多维表格（Bitable） | 支持 | / | / |
  | 电子表格（Sheet） | 支持 | / | / |
  | 思维笔记（Mindnote） | 不支持 | / | / |
  | UML 图（Diagram） | 不支持 | 不支持 | 不支持 |
  | 引用容器（QuoteContainer） | 支持 | 支持 | 支持 |
  | 任务（Task） | 不支持 | / | / |
  | OKR | 支持 | 支持 | / |
  | OKR 目标（OkrObjective） | / | 支持 | / |
  | OKR 关键结果（OkrKeyResult） | / | 支持 | / |
  | OKR 进展（OkrProgress） | / | 支持 | / |
  | 文档小组件（AddOns） | 支持 | 支持 | / |
  | Jira 问题（JiraIssue） | / | 支持 | / |
  | Wiki 子页面列表（旧版）（WikiCatalog） | 支持 | / | / |
  | 画板（Board） | 支持 | 支持 | / |
  | 议程（Agenda）| 不支持 | 支持 | / |
  | 议程项（AgendaItem）| / | 支持 | / |
  | 议程项标题（AgendaItemTitle）| / | 支持 | 不支持 |
  | 议程项内容（AgendaItemContent）| / | 支持 | / |
  | 链接预览（LinkPreview）| 支持 | 不支持 | / |
  | 源同步块（SourceSynced）| 不支持 | 支持 | / |
  | 引用同步块（ReferenceSynced）| 不支持 | 支持 | / |
  | Wiki 子页面列表（新版）（SubPageList）| 支持 | / | / |
  | AI 模板（AITemplate）| 不支持 | / | 不支持 |
  | 未定义块（Undefined） | / | / | / |

## 接入流程

接入文档 OpenAPI 的流程如下图所示。了解更多，参考[云文档-概述](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/docs-overview) 的 **接入流程** 一节。

![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/42967c08b5e6619841ebd673f8e66f17_TRmROny4AI.png?height=546&lazyload=true&width=6382)

## 方法列表

以下为文档和块的 OpenAPI 列表。

### 文档

<b>方法 (API) | <b>权限要求（满足任一） | <b>访问凭证 | <b>商店 | <b>自建
---|---|---|---|---
`GET` 获取文档基本信息<br>[/open-apis/docx/v1/documents/:document_id](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/get) | 创建及编辑新版文档(docx:document)<br>查看新版文档(docx:document:readonly) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
`GET` 获取文档纯文本内容<br>[/open-apis/docx/v1/documents/:document_id/raw_content](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/raw_content) | 创建及编辑新版文档(docx:document)<br>查看新版文档(docx:document:readonly) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
`GET` 获取文档所有块<br>[/open-apis/docx/v1/documents/:document_id/blocks](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list) | 创建及编辑新版文档(docx:document)<br>查看新版文档(docx:document:readonly) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
`POST` 创建文档<br>[/open-apis/docx/v1/documents](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/create) | 创建及编辑新版文档(docx:document) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**

### 块

<b>方法 (API) | <b>权限要求（满足任一） | <b>访问凭证 | <b>商店 | <b>自建
---|---|---|---|---
`GET` 获取块<br>[/open-apis/docx/v1/documents/:document_id/blocks/:block_id](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/get) | 创建及编辑新版文档(docx:document)<br>查看新版文档(docx:document:readonly) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
`POST` 创建块<br>[/open-apis/docx/v1/documents/:document_id/blocks/:block_id/children](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create) | 创建及编辑新版文档(docx:document) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
`POST` 创建嵌套块<br>[/open-apis/docx/v1/documents/:document_id/blocks/:block_id/descendant](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-descendant/create) | 创建及编辑新版文档(docx:document) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
`PATCH` 更新块<br>[/open-apis/docx/v1/documents/:document_id/blocks/:block_id](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/patch) | 创建及编辑新版文档(docx:document) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
`PATCH` 批量更新块<br>[/open-apis/docx/v1/documents/:document_id/blocks/batch_update](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/batch_update) | 创建及编辑新版文档(docx:document) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
`DELETE` 删除块<br>[/open-apis/docx/v1/documents/:document_id/blocks/:block_id/children/batch_delete](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/batch_delete) | 创建及编辑新版文档(docx:document) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
`GET` 获取所有子块<br>[/open-apis/docx/v1/documents/:document_id/blocks/:block_id/children](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/get) | 创建及编辑新版文档(docx:document)<br>查看新版文档(docx:document:readonly) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
# 文档常见问题

## 1.  如何插入带内容的表格（table）？

- 方式一：调用[创建嵌套块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-descendant/create)接口，在指定的 Parent Block 下创建 Table Block：

```bash
  curl --location --request POST 'https://open.feishu.cn/open-apis/docx/v1/documents/:document_id/blocks/:block_id/descendant?document_revision_id=-1' \
  --header 'Authorization: Bearer u-xxxx' \
  --header 'Content-Type: application/json; charset=utf-8' \
  --data-raw '{
      "index": 0,
      "children_id": [
          "headingid_1",
          "table_id_1"
      ],
      "descendants": [
          {
              "block_id": "headingid_1",
              "block_type": 3,
              "heading1": {
                  "elements": [{"text_run": {"content" : "简单表格"}}]
              },
              "children": []
          },
          {
              "block_id":"table_id_1",
              "block_type": 31,
              "table":{
                  "property" : {
                  "row_size": 1,
                  "column_size" : 2
                  }
              },
              "children": ["table_cell1","table_cell2"]
          },
          {
              "block_id": "table_cell1",
              "block_type": 32,
              "table_cell":{},
              "children": ["table_cell1_child1", "table_cell1_child2"]
          },
          {
              "block_id": "table_cell2",
              "block_type": 32,
              "table_cell":{},
              "children": ["table_cell2_child"]
          },
          {
              "block_id": "table_cell1_child1",
              "block_type": 13,
              "ordered": {
                  "elements": [{"text_run": {"content" : "list 1.1"}}]
              },
              "children": []
          },
          {
              "block_id": "table_cell1_child2",
              "block_type": 13,
              "ordered": {
                  "elements": [{"text_run": {"content" : "list 1.2"}}]
              },
              "children": []
          },
          {
              "block_id": "table_cell2_child",
              "block_type": 2,
              "text": {
                  "elements": [{"text_run": {"content" : ""}}]
              },
              "children": []
          }
      ]
  }'
  # 调用前请替换 'Authorization: Bearer u-xxx' 中的 'u-xxx' 为真实的访问令牌
  ```
  在上述示例中，我们成功地创建了一个一级标题块，其内容为 “简单表格”，同时还创建了一个带有具体内容的表格块。

内容如下所示：

![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/d5b6bfc6c86b2db19a5c49200e812c97_gOGa74B4oH.png?height=310&lazyload=true&width=1670)

- 方式二：先创建一个空表格，再填充内容：

1. 调用 [创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create) 接口，在指定 Parent Block 下创建一个 Table Block。

```bash
  curl --location --request POST '{url}' \
  --header 'Authorization: {Authorization}' \
  --header 'Content-Type: application/json' \
  --data-raw '{
      "index": 0,
      "children": [
          {
              "block_type": 31,
              "table": {
                  "property": {
                      "row_size": 1,
                      "column_size": 1
                  }
              }
          }
      ]
  }'
  ```
  在上述示例中，我们创建了一个 1 行 1 列的表格，如果调用成功，预计会返回下列格式数据：

```json
  {
      "code": 0,
      "data": {
          "children": [
              {
                  "block_id": "......",
                  "block_type": 31,
                  "children": [
                      // 单元格 BlockID 数组，按从左到右从上到下顺序排列
                      "......"
                  ],
                  "parent_id": "......",
                  "table": {
                      "cells": [
                          "......"
                      ],
                      "property": {
                          "column_size": 1,
                          "column_width": [
                              100
                          ],
                          "merge_info": [
                              {
                                  "col_span": 1,
                                  "row_span": 1
                              }
                          ],
                          "row_size": 1
                      }
                  }
              }
          ],
          ......
      },
      "msg": ""
  }
  ```

其中 data.children 数组中存放了按照从左到右、从上到下顺序遍历得到的单元格 Table Cell 的 Block ID。接下来，你可继续调用[创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create)接口，指定 Table Block 为 Parent Cell，对指定单元格添加内容。
## 2. 如何插入电子表格（sheet）并往单元格填充内容？

1. 调用 [创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create) 接口，在指定 Parent Block 下创建 Sheet Block，指定电子表格的行数量和列数量。
    ```bash
    curl --location --request POST 'https://{domain}/open-apis/docx/v1/documents/:document_id/blocks/:block_id/children' \
    --header 'Authorization: {Authorization}' \
    --header 'Content-Type: application/json' \
    --data-raw '{
      {
        "index": 0,
        "children": [
          {
            "block_type": 30,
            "sheet": {
              "row_size": 5,
              "column_size": 3
            }
          }
        ]
      }
    }'
    ```	

在上述示例中，我们创建了一个 5 行 3 列的表格，如果调用成功，预计会返回下列格式数据。

```json
        {
          "code": 0,
          "data": {
            "children": [
              {
                "block_id": "doxcnx8mv0hzeY07TUlKzpabcef",
                "block_type": 30,
                "parent_id": "UFZvdKi97ojvkzx3ZZocklabcef",
                "sheet": {
                  "token": "LxvrsycFwhQYfrt8oYQcwVabcef_QJ6HZR" // 电子表格 token + 工作表 ID 格式
                }
              }
            ],
            "client_token": "f098d96e-693b-442f-8a7d-82c309ebc500",
            "document_revision_id": 54
          },
          "msg": "success"
        }
    ```

2. 返回的 `sheet.token` 的值为电子表格的 token 和电子表格工作表的 ID 的组合。你可继续调用[电子表格相关接口](https://open.feishu.cn/document/ukTMukTMukTM/uATMzUjLwEzM14CMxMTN/overview)继续操作该表格。以下示例展示在该电子表格中写入数据。
    ```bash
    curl --location --request PUT 'https://open.feishu.cn/open-apis/sheets/v2/spreadsheets/LxvrsycFwhQYfrt8oYQcwVabcef/values' \
    --header 'Authorization: Bearer t-g10474apW3IFUPQGV362IPSAGELJO2SQWL5abcef' \
    --header 'Content-Type: application/json' \
    --data-raw '{
    "valueRange":{
        "range": "QJ6HZR!A1:B2",
        "values": [
          [
            "Hello", 1
          ],
          [
            "World", 1
          ]
        ]
        }
    }'
    ```
    如果调用成功，预计将返回以下数据：
    ```json
    {
      "code": 0,
      "data": {
        "revision": 2,
        "spreadsheetToken": "LxvrsycFwhQYfrt8oYQcwVabcef",
        "updatedCells": 4,
        "updatedColumns": 2,
        "updatedRange": "QJ6HZR!A1:B2",
        "updatedRows": 2
      },
      "msg": "success"
    }
    ```

## 3. 如何插入图片？

**第一步：创建图片 Block**

调用 [创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create) 接口，在指定的 Parent Block 下创建 Image Block：

```bash
curl --location --request POST '{url}' \
--header 'Authorization: {Authorization}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "index": 0,
  "children": [
    {
      "block_type": 27,
      "image": {}
    }
  ]
}'
```

如果调用成功，预计会返回下列格式数据：

```json
{
    "code": 0,
    "data": {
        "children": [
            {
                "block_id": "doxcnEUmKKppwWrnUIcgZ2ibc9g",
                // Image BlockID
                "block_type": 27,
                "image": {
                    "height": 100,
                    "token": "",
                    "width": 100
                },
                "parent_id": "doxcnQxzmNsMl9rsJRZrCpGx71e"
            }
        ],
        "client_token": "bc25a4f0-9a24-4ade-9ca2-6c1db43fa61d",
        "document_revision_id": 7
    },
    "msg": ""
}
```

**第二步：上传图片素材**

调用 [上传图片素材](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/media/upload_all) 接口，使用步骤一返回的 Image BlockID 作为 `parent_node` 上传素材：

```bash
curl --location --request POST '{url}' \
--header 'Authorization: {Authorization}' \
--header 'Content-Type: multipart/form-data; boundary=---7MA4YWxkTrZu0gW' \
--form 'file=@"/tmp/test.PNG"' \ # 图片本地路径
--form 'file_name="test.PNG"' \ # 图片名称
--form 'parent_type="docx_image"' \ # 素材类型为 docx_image
--form 'parent_node="doxcnEUmKKppwWrnUIcgZ2ibc9g"' \ # Image BlockID
--form 'size="xxx"' # 图片大小
```

如果调用成功，预计会返回下列格式数据：

```json
{
    "code": 0,
    "data": {
        "file_token": "boxbckbfvfcqEg22hAzN8Dh9gJd" // 图片素材 ID
    },
    "msg": "Success"
}
```

**第三步：设置图片 Block 的素材**

调用 [更新块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/patch) 或 [批量更新块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/batch_update) 接口，指定 `replace_image` 操作，将步骤二返回的图片素材 ID 设置到对应的 Image Block，以更新块为例：

``` bash
curl --location --request PATCH '{url}' \
--header 'Authorization: {Authorization}' \
--header 'Content-Type: application/json' \
--data-raw '{
    "replace_image": {
        "token": "boxbckbfvfcqEg22hAzN8Dh9gJd" # 图片素材 ID
    }
}'
```

## 4. 如何插入文件/附件？

**第一步：创建一个空的文件 Block**

调用 [创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create) 接口，在指定 Parent Block 下创建一个空的 File Block：

```bash
curl --location --request POST '{url}' \
--header 'Authorization: {Authorization}' \
--header 'Content-Type: application/json' \
--data-raw '{
    "index": 0,
    "children": [
        {
            "block_type": 23,
            "file": {
                "token": ""
            }
        }
    ]
}'
```

如果调用成功，预计会返回下列格式数据，从中可获取到该空 File Block 的 ID `doxcn1Bx1WOlcqzLqTD2UUYiA7g`：

```json
{
    "code": 0,
    "data": {
        "children": [
            {
                "block_id": "doxcnIfCrxq7MlhDbj8xCXmPXgf", // View Block 的 ID
                "block_type": 33,
                "children": [
                    "doxcn1Bx1WOlcqzLqTD2UUYiA7g" // File Block 的 ID
                ],
                "parent_id": "doxcnQxzmNsMl9rsJRZrCpGx7ze",
                "view": {
                    "view_type": 1
                }
            }
        ],
        "client_token": "07c56d36-db8b-480f-97f2-7b77a9d3e787",
        "document_revision_id": 8
    },
    "msg": ""
}
```
**注意事项**：**注意：** 与 Image Block 不同，在创建 File Block 成功后，接口会返回 View Block，这是因为每个 File Block 对应都会有一个 View Block 来控制其视图形式，即 View Block 是 File Block 的 Parent。

**第二步：上传文件素材**

调用[上传素材](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/media/upload_all)接口，使用步骤一返回的 File Block 的 ID `doxcn1Bx1WOlcqzLqTD2UUYiA7g` 作为 `parent_node` 的值，将素材文件上传至该 File Block 中：

```bash
curl --location --request POST '{url}' \
--header 'Authorization: {Authorization}' \
--header 'Content-Type: multipart/form-data; boundary=---7MA4YWxkTrZu0gW' \
--form 'file=@"/tmp/test.PNG"' \ # 文件本地路径
--form 'file_name="test.PNG"' \ # 文件名称
--form 'parent_type="docx_file"' \ # 素材类型为 docx_file
--form 'parent_node="doxcn1Bx1WOlcqzLqTD2UUYiA7g"' \ # File Block 的 ID
--form 'size="xxx"' # 文件大小
```

如果调用成功，预计会返回下列格式数据，从中可获取到已成功上传的文件的 ID：

```json
{
    "code": 0,
    "data": {
        "file_token": "boxbcXvrJyOMX6EhmGF1bkoQwOb" // 文件素材 ID
    },
    "msg": "Success"
}
```

**第三步：设置文件 Block 的素材**

调用 [更新块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/patch) 或 [批量更新块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/batch_update) 接口，指定 `replace_file` 操作，将步骤二返回的素材 ID 设置到对应的 File Block。以更新块为例：

```bash
## 注意 URL 中的 block_id 路径参数需要与步骤一创建的 File Block ID 一致
## https://{domain}/open-apis/docx/v1/documents/:document_id/blocks/doxcn1Bx1WOlcqzLqTD2UUYiA7g

curl --location --request PATCH '{url}' \
--header 'Authorization: {Authorization}' \
--header 'Content-Type: application/json' \
--data-raw '{
    "replace_file": {
        "token": "boxbcXvrJyOMX6EhmGF1bkoQwOb" # 文件素材 ID
    }
}'
```
## 5. 如何插入@用户 元素？
**注意事项**：通过调用 OpenAPI 来 @用户，不会向该用户发送通知。

@用户是 Text Block 中的一个内容实体。如果要 @某个用户，可以调用 [创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create)接口，在指定父亲 Block 下创建 Text Block，并在 Text Block 中指定要 @ 的用户 ID：
```json

# https://{domain}/open-apis/docx/v1/documents/:document_id/blocks/:block_id/children?document_revision_id=-1

curl --location --request POST '{url}' \
--header 'Content-Type: application/json' \
--header 'Authorization: {Authorization}' \
--data-raw '{
    "children": [
        {
            "block_type": 2,
            "text": {
                "elements": [
                    {
                        "mention_user": {
                            "text_element_style": {
                                "bold": false,
                                "inline_code": false,
                                "italic": false,
                                "strikethrough": false,
                                "underline": false
                            },
                            "user_id": "{user_id}"
                        }
                    }
                ],
                "style": {
                    "align": 1,
                    "folded": false
                }
            }
        }
    ],
    "index": 0
}'
```
在上述示例中，在`document_id` 这篇文档指定的`block_id` 下，创建了一个 Child Block，该 Child Block 是一个 Text Block，并且其中有一个`mention_user` 的文本元素 @ 了指定用户，用户的 ID 为 `user_id`，如果调用成功，预计会返回下列格式数据：
```json
{
  "code": 0,
  "data": {
    "children": [
      {
        "block_id": "......",
        "block_type": 2,
        "parent_id": "......",
        "text": {
          "elements": [
            {
              "mention_user": {
                "text_element_style": {
                  "bold": false,
                  "inline_code": false,
                  "italic": false,
                  "strikethrough": false,
                  "underline": false
                },
                "user_id": "......"
              }
            }
          ],
          "style": {
            "align": 1,
            "folded": false
          }
        }
      }
    ],
    ......
  },
  "msg": "success"
}
```
## 6. 如何插入一个公式？

公式不是一个 Block，其是 Text Block 下的一个 Element，结构体如下：

```json
{
    "content": string,
    "text_element_style": object(TextElementStyle)
}
```
如要向文档插入一个公式，可调用[创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create)接口，请求体示例如下：

```json
{
  "index": 0,
  "children": [
    {
      "block_type": 2,
      "text": {
        "elements": [
          {
            "equation": {
              "content": "1+2=3\n",
              "text_element_style": {
                "bold": false,
                "inline_code": false,
                "italic": false,
                "strikethrough": false,
                "underline": false
              }
            }
          }
        ],
        "style": {
          "align": 1,
          "folded": false
        }
      }
    }
  ]
}
```
## 7. 如何往高亮块（Callout Block）中填充内容？

调用 [创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create)接口，其中路径参数 `block_id` 填写 Callout BlockID，请求体 `children` 填充高亮块的内容。例如，在高亮块内容的第一行插入文本块：
```json
curl --location --request POST '{url}' \
--header 'Authorization: {Authorization}' \ 
--header 'Content-Type: application/json' \
--data-raw '{
    "index": 0,
    "children": [
        {
            "block_type": 2,
            "text": {
                "elements": [
                    {
                        "text_run": {
                            "content": "多人实时协同编辑，一切元素都可插入。",
                            "text_element_style": {
                                "background_color": 14,
                                "text_color": 5
                            }
                        }
                    },
                    {
                        "text_run": {
                            "content": "不仅是在线文档，更是强大的创作和互动工具。",
                            "text_element_style": {
                                "background_color": 14,
                                "bold": true,
                                "text_color": 5
                            }
                        }
                    }
                ],
                "style": {}
            }
        }
    ]
}'
```
## 8. 如何插入分栏块（Grid block）并在第一栏中插入内容？

**第一步：创建 Grid block**

调用 [创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create) 接口，在指定 Parent block 下创建 Grid block，该 Grid 共计有两列。

**Request**
```bash
# https://{domain}/open-apis/docx/v1/documents/:document_id/blocks/:block_id/children
curl --location --request POST '{url}' \
--header 'Authorization: {Authorization}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "index": 0,
  "children": [
    {
      "block_type": 24,
      "grid": {
        "column_size": 2
      }
    }
  ]
}'
```

**Response**
**注意事项**：在创建 Grid block 成功后，接口会返回 Grid block 的 `block_id` 以及 `children` 等，`children` 即 Grid Column Block，由于 Request 指定要创建两列，因此 `children` 数组中会有两个`block_id`，接下来可以使用这些`block_id`往 Grid Column block 中继续添加 Children block。

```bash
{
  "code": 0,
  "data": {
    "children": [
      {
        "block_id": "doxcn7VulseZpcWivDsfNi7tPAf",
        "block_type": 24,
        "children": [
          "doxcnVDmCQuoiQPJUXuaYJnEeBe", // 第一个 Grid Column Block
          "doxcnR4tyA3dJn9MWxa1VrxsKRc"  // 第二个 Grid Column Block
        ],
        "grid": {
          "column_size": 2
        },
        "parent_id": "Xrt5aEe0DoKTslxIqBRcIEAJnBc"
      }
    ],
    "client_token": "bef26316-0079-4f26-995e-447004dd996a",
    "document_revision_id": 85
  },
  "msg": "success"
}
```

**第二步：在第一列 Grid Column Block 中插入内容**

调用[创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create)接口，在指定 Grid Column Block 下插入一个文本 Block。

**Request**

```bash
# https://{domain}/open-apis/docx/v1/documents/:document_id/blocks/:block_id/children
curl --location --request POST '{url}' \
--header 'Authorization: {Authorization}' \
--header 'Content-Type: application/json' \
--data-raw '{
  "index": 0,
  "children": [
    {
      "block_type": 2,
      "text": {
        "elements": [
          {
            "text_run": {
              "content": "多人实时协同，插入一切元素。不仅是在线文档，更是强大的创作和互动工具",
              "text_element_style": {
                "background_color": 14,
                "text_color": 5
              }
            }
          }
        ],
        "style": {}
      }
    }
  ]
}'
```

**Response**
**注意事项**：在第一步创建 Grid Block 时，系统会自动往每个 Grid Column Block 下添加一个空 Text Block，如果不需要默认的空白 Text Block，可以在第 2 步添加完内容后，自行删除该 Text Block。

```bash
{
  "code": 0,
  "data": {
    "children": [
      {
        "block_id": "doxcnT2booYsWL6XsAcyl958nye",
        "block_type": 2,
        "parent_id": "doxcnVDmCQuoi1PJUXuTYJnEeBe",
        "text": {
          "elements": [
            {
              "text_run": {
                "content": "多人实时协同，插入一切元素。不仅是在线文档，更是强大的创作和互动工具",
                "text_element_style": {
                  "background_color": 14,
                  "bold": false,
                  "inline_code": false,
                  "italic": false,
                  "strikethrough": false,
                  "text_color": 5,
                  "underline": false
                }
              }
            }
          ],
          "style": {
            "align": 1,
            "folded": false
          }
        }
      }
    ],
    "client_token": "b09b2539-487b-42f3-b747-f12ab177bb13",
    "document_revision_id": 86
  },
  "msg": "success"
}
```
## 9. 如何获取文档中的图片&附件？

1. 调用[获取文档所有块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list)接口，分页获取文档所有块的富文本内容。
    ```bash
    curl --location 'https://open.feishu.cn/open-apis/docx/v1/documents/:document_id/blocks' \
    --header 'Authorization: {Authorization}'
    ```
    此接口为分页接口，如果 has_more 为 true，则表示下次遍历时可采用返回值中的 page_token 查询下一分页的文档内容。
在上述用例中，我们获取了文档第一分页中块的富文本内容，如果调用成功，预计会返回下列格式数据。
```json
{
    "code": 0,
    "data": {
        "has_more": true,
        "page_token": "aw7DoMKBFMOGwqHCrcO8w6jCmMOvw6ILeADCvsKNw57Di8O5XGV3LG4_w5HCqhFxSnDCrCzCn0BgZcOYUg85EMOYcEAcwqYOw4ojw5QFwofCu8KoIMO3K8Ktw4IuNMOBBHNYw4bCgCV3U1zDu8K-J8KSR8Kgw7Y0fsKZdsKvW3d9w53DnkHDrcO5bDkYwrvDisOEPcOtVFJ-I03CnsOILMOoAmLDknd6dsKqG1bClAjDuS3CvcOTwo7Dg8OrwovDsRdqIcKxw5HDohTDtXN9w5rCkWo",
        "items": [
            {
                "block_id": "AZEUdA02Qo3uuWxjVo7cEyNJnLf",
                "block_type": 1,
                "children": [
                    "MQFydWYYCoEDdpxiq4kcjHZ0noW",
                    "OTZtdNzhFoXOWlxd4BkcKO4on2d"
                ],
                "page": {
                    "elements": [
                        {
                            "text_run": {
                                "content": "精美图集",
                                "text_element_style": {
                                    "bold": false,
                                    "inline_code": false,
                                    "italic": false,
                                    "strikethrough": false,
                                    "underline": false
                                }
                            }
                        }
                    ],
                    "style": {
                        "align": 1
                    }
                },
                "parent_id": ""
            },
            {
                "block_id": "MQFydWYYCoEDdpxiq4kcjHZ0noW",
                "block_type": 27, // block_type: image
                "image": {
                    "align": 2,
                    "height": 1200,
                    "token": "HbuhbbMDBoNf1AxZt0Cc6nR6nSe", // image token
                    "width": 4800
                },
                "parent_id": "AZEUdA02Qo3uuWxjVo7cEyNJnLf"
            },
            {
                "block_id": "OTZtdNzhFoXOWlxd4BkcKO4on2d",
                "block_type": 33, // block_type: view
                "children": [
                    "I90UdpixCo6ZDOxE7dscMWlRn3e"
                ],
                "parent_id": "AZEUdA02Qo3uuWxjVo7cEyNJnLf",
                "view": {
                    "view_type": 1
                }
            },
            {
                "block_id": "I90UdpixCo6ZDOxE7dscMWlRn3e",
                "block_type": 23, // block_type: file
                "file": {
                    "name": "image.png",
                    "token": "KNm7bdTXooqUNAx52ZWcBR0Enib" // file token
                },
                "parent_id": "OTZtdNzhFoXOWlxd4BkcKO4on2d"
            }
        ]
    },
    "msg": "success"
}
```
2. 在返回数据中：
    * `"block_type": 27` 的块为图片块，块中 `image.token` 的值为图片的 token。
    * `"block_type": 23` 的块为文件块，块中 `file.token` 的值为文件的 token。

你可基于图片和文件的 token，调用[下载素材](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/media/download)接口下载对应的图片和文件。
## 10. 如何将 markdown 格式的内容写进飞书在线文档？

若要将 Markdown/HTML 格式的内容写入到文档，需依次执行以下操作：

1. 调用[创建文档](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/create)接口创建一篇类型为 docx 的文档（若目标文档已存在，则无需此步骤）。
2. 调用[转换为文档块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/convert)接口将 Markdown/HTML 格式的内容转换为文档块。
3. 调用[创建嵌套块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-descendant/create)接口将步骤二中返回的块批量插入到目标文档中。

**在上述接口调用过程中需注意以下事项：**

- 将带表格的 Markdown/HTML 格式的内容转换为文档块后，在调用[创建嵌套块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-descendant/create)接口批量插入块到文档前，需先去除表格（Table）块中的 `merge_info` 字段。由于当前 `merge_info` 为只读属性，传入该字段会引发报错。

- 将包含图片的 Markdown/HTML 格式的内容转换为文档块，并调用[创建嵌套块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-descendant/create)接口将图片（Image）块插入到文档后，需调用[上传图片素材](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/media/upload_all)接口，以 Image BlockID 作为 `parent_node` 上传素材，接着调用[更新块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/patch)或[批量更新块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/batch_update)接口，指定 `replace_image` 操作，将图片素材 ID 设置到对应的 Image Block。

- 当转换后的块数量过多时，需分批调用[创建嵌套块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-descendant/create)接口，单次调用[创建嵌套块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-descendant/create)接口最多可插入 1000 个块。
## 11. 服务端 OpenAPI 接口限频阈值是多少？

具体请查阅对应接口文档，比如 [更新块的内容](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/patch)接口频率限制为每个应用 3 次/秒。
## 12. 文档 OpenAPI 支持哪些类型 Block？

具体请查阅 [块的数据结构](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/data-structure/block) 中 BlockType  小节。

## 13. 新创建的文档还没有 Block，该如何添加 Block ？

新创建的文档有 Block，该 Block 为 Page Block。

创建空文档成功后，接口会返回 `document_id`，`document_id`也是该文档页面块（Page Block）的 `block_id`，因此你可以通过指定 `document_id` 调用 [创建块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/create)接口来添加 Block。

## 14. 获取文档所有块接口是按什么顺序返回 Block 的？

[获取文档所有块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list)接口返回的 items 是一个 [1,N] (N>=1) 的 Block 数组。数组中元素的次序按文档内容先序遍历结果进行排列，其中索引为 0 的元素是文档根节点。

![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/f2781a250e0532e5d09fed46574eecd0_bnsLLioGHI.png?height=436&lazyload=true&width=1123)

以上图为例，其 Blocks 先序遍历结果为：

![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/83dda0898d4d82bc4cb8e4b71c7e0544_m1p0yCU21p.png?height=164&lazyload=true&width=923)

## 15. 如何更新文档标题？

文档中的 Block 之间是树状关系，树的根 Block 是 Page Block，文档标题是 Page Block 的文本属性，并且 Page Block 的 BlockID 就是文档的 Token，因此若要更新文档标题，请调用 [更新块的内容](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/patch)接口，并指定为 `update_text_elements` 或 `update_text` 操作，其中请求的路径参数：

- `document_id`：填写新版文档的 Token，即 Page Block 的 BlockID
- `block_id`：填写新版文档的 Token，即 Page Block 的 BlockID
```bash
curl --location --request PATCH '{url}' \
--header 'Content-Type: application/json' \
--header 'Authorization: {Authorization}' \
--data-raw '{
    "update_text_elements": {
        "elements": [
            {
                "text_run": {
                    "content": "New Title" 新标题
                }
            }
        ]
    }
}'
```
## 16. 文档有服务端的 SDK 吗？
**注意事项**：SDK 的建设滞后于最新的 API，比如 API 已支持返回某新类型的 Block，但 SDK 尚未支持解析，但会保证其向前兼容。

目前 SDK 支持 Java、Python、Go 和 Node.js 语言：

**Java**

- GitHub 代码托管地址：[larksuite/oapi-sdk-java](https://github.com/larksuite/oapi-sdk-java/tree/main/larksuite-oapi/src/main/java/com/larksuite/oapi/service/docx/v1)
- 使用指引：[GitHub - larksuite/oapi-sdk-java](https://github.com/larksuite/oapi-sdk-java)

**Python**

- GitHub 代码托管地址：[larksuite/oapi-sdk-python](https://github.com/larksuite/oapi-sdk-python/tree/main/src/larksuiteoapi/service/docx)
- 使用指引：[GitHub - larksuite/oapi-sdk-python](https://github.com/larksuite/oapi-sdk-python)

**Go**

- GitHub 代码托管地址：[larksuite/oapi-sdk-go](https://github.com/larksuite/oapi-sdk-go/tree/v3_main/service/docx)
- 使用指引：[GitHub - larksuite/oapi-sdk-go](https://github.com/larksuite/oapi-sdk-go)

**Node.js**

- GitHub 代码托管地址：[larksuite/oapi-sdk-node.js](https://github.com/larksuite/node-sdk/blob/main/code-gen/projects/docx.ts)
- 使用指引：[GitHub - larksuite/oapi-sdk-node.js](https://github.com/larksuite/node-sdk/blob/main/README.zh.md)
## 17. 如何直接通过云文档模板创建文档？

模板其实也是一篇文档，可以通过其链接中的 `document_id` 调用 [复制文件](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/file/copy) 接口创建出一篇新文档。
如下图，假定「工作周报」该模板的访问链接是 `https://{domain}/docx/ke6jdf477ohCVVxzANnc56abcef`，那么你可通过 `ke6jdf477ohCVVxzANnc56abcef` 这个 `document_id` 去复制文件。

![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/7a3f03605ba97f77371997814f9c38de_Nty18gpw48.png?height=373&lazyload=true&maxWidth=650&width=1272)

## 18. 文档 OpenAPI 有哪些限制?

较之旧版文档的 OpenAPI，新版 OpenAPI 不支持带内容创建文档。不支持的主要原因是构建及维护正确的嵌套 Block 关系对开发者的要求较高。推荐你使用导入、创建副本等 API 来满足带内容创建的场景。

## 19. 如何读取文档中电子表格的内容，并继续插入一行数据？

1. 调用 [获取文档所有块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list)接口，获取电子表格块的 token。若调用成功，预计将返回以下格式数据。

其中返回的 `sheet.token` 的值 `B3hasMxsshByaEtZxAwcVfWxnSe_Ml1QzO` 为电子表格的唯一标识（spreadsheet_token）和电子表格工作表的唯一标识（sheet_id）的组合。

```json
    {
      "code": 0,
      "data": {
        "has_more": false,
        "items": [
          {
            "block_id": "RMDydlSOLojiUEx0SROcA4fdn5d",
            "block_type": 1,
            "children": [
              "XpvLdPiaxoBM08xhyfEcVZj7nlc"
            ],
            "page": {
              "elements": [
                {
                  "text_run": {
                    "content": "一篇文档",
                    "text_element_style": {
                      "bold": false,
                      "inline_code": false,
                      "italic": false,
                      "strikethrough": false,
                      "underline": false
                    }
                  }
                }
              ],
              "style": {
                "align": 1
              }
            },
            "parent_id": ""
          },
          {
            "block_id": "XpvLdPiaxoBM08xhyfEcVZj7nlc",
            "block_type": 30,
            "parent_id": "RMDydlSOLojiUEx0SROcA4fdn5d",
            "sheet": {
              "token": "B3hasMxsshByaEtZxAwcVfWxnSe_Ml1QzO"  // 电子表格的唯一标识（spreadsheet_token）和电子表格工作表的唯一标识（sheet_id）的组合
            }
          }
        ]
      },
      "msg": "success"
    }
    ```

1. 基于步骤一获取的电子表格的唯一标识（spreadsheet_token）和电子表格工作表的唯一标识（sheet_id），调用电子表格的[读取单个范围](https://open.feishu.cn/document/ukTMukTMukTM/ugTMzUjL4EzM14COxMTN)接口，获取表格中的数据。了解请求示例和响应体示例请直接参考该接口文档。

1. 基于步骤一获取的电子表格的唯一标识（spreadsheet_token）和电子表格工作表的唯一标识（sheet_id），调用电子表格的[插入数据](https://open.feishu.cn/document/ukTMukTMukTM/uIjMzUjLyIzM14iMyMTN)接口，在指定范围的起始位置上方插入数据。了解请求示例和响应体示例请直接参考该接口文档。

## 20. 如何调用接口对文档中的多维表格进行调整？

1. 调用[获取文档所有块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list)接口，获取多维表格块的 token。若调用成功，预计将返回以下格式数据。

其中返回的 `bitable.token` 的值`MMLLb4qYna4FrgsX5THc6EOTnT2_tblacTqz7wOURGpd` 为多维表格的唯一标识（app_token）和多维表格数据表的唯一标识（table_id）的组合。

```json
    {
      "code": 0,
      "data": {
        "has_more": false,
        "items": [
          {
            "block_id": "Fu2Bd6f6ToLrnUxLGsPcLbwQned",
            "block_type": 1,
            "children": [
              "PBindydNxoJTEvx4ll2cu0ZDnqf"
            ],
            "page": {
              "elements": [
                {
                  "text_run": {
                    "content": "业务经营周报",
                    "text_element_style": {
                      "bold": false,
                      "inline_code": false,
                      "italic": false,
                      "strikethrough": false,
                      "underline": false
                    }
                  }
                }
              ],
              "style": {
                "align": 1
              }
            },
            "parent_id": ""
          },
          {
            "bitable": {
              "token": "MMLLb4qYna4FrgsX5THc6EOTnT2_tblacTqz7wOURGpd"
            },
            "block_id": "PBindydNxoJTEvx4ll2cu0ZDnqf",
            "block_type": 18,
            "parent_id": "Fu2Bd6f6ToLrnUxLGsPcLbwQned"
          }
        ]
      },
      "msg": "success"
    }
    ```

1. 基于步骤一获取的多维表格的唯一标识（app_token）和多维表格数据表的唯一标识（table_id），调用[多维表格相关接口](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/bitable-overview#791c8e74)，对多维表格进行操作。

## 21. 如何获取源同步块的内容？
文档中直接创建的同步块称为源同步块，源同步块的内容在其子孙列表中，可以通过[获取文档所有块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list)接口直接拿到。

## 22. 如何获取引用同步块的内容？
通过复制粘贴得到的同步块称为引用同步块，可先通过[获取文档所有块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list)接口获取到引用同步块，引用同步块中记录了其引用的源同步块的文档 ID 和 Block ID。
```json
{
    "block_id": "QtLFdCudXo96tPxFbtKcb9abcef",
    "block_type": 50,
    "parent_id": "WCR8dI68OoFVb9xk6kYcE3abcef",
    "reference_synced":
    {
        "source_block_id": "Zn9jdf1OqsMeUxbAhjXcqiabcef",   // 源同步块 ID
        "source_document_id": "WCR8dI68OoFVb9xk6kYcE3abcef" // 源文档 ID 
    }
}
```
可使用 `source_document_id` 和 `source_block_id` 调用 [获取所有子块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block-children/get)接口，将查询参数 `with_descendant` 指定为 `true` 获取引用的源同步块的子孙块内容。
<md-alert>
以应用身份(`tenant_access_token`)获取引用的源同步块内容时，需要应用有源文档的阅读权限。

以用户身份(`user_access_token`)获取引用的源同步块内容时，需要用户有同步块的阅读权限。

查询同步块历史版本，需要有源文档的编辑权限。

```bash
curl -i -X GET 'https://open.feishu.cn/open-apis/docx/v1/documents/WCR8dI68OoFVb9xk6kYcE3abcef/blocks/Zn9jdf1OqsMeUxbAhjXcqiabcef/children?with_descendants=true' \
-H 'Authorization: Bearer u-xxxx'
```
