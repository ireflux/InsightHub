# 知识库概述

飞书知识库是一个面向组织的知识管理系统。通过结构化沉淀高价值信息，形成完整的知识体系。此外，明确的内容分类，层级式的页面树，还能够轻松提升知识的流转和传播效率，更好地成就组织和个人。

资源 | 资源定义
---|---
**知识空间** | 用于管理文件和其它文件夹的容器。
**节点** | 知识空间中的节点，支持文档、表格等多种文件类型。

你可以通过知识库 API，来自动化管理你的知识库。
在调用知识库 API 之前，请确保你的应用已经按需申请了以下权限并发布：
- `wiki:wiki`: 可以对知识库进行增删改查
- `wiki:wiki.readonly`: 可以读取知识库内容，无法编辑或修改知识库

相关说明详见：[应用权限](https://open.feishu.cn/document/ukTMukTMukTM/uQjN3QjL0YzN04CN2cDN)

## 资源：知识空间 Workspace
知识空间是知识库的基本组成单位，是企业根据需要搭建的不同类别的知识体系，由多个具有层级和所属关系的文档页面构成。每个知识空间，都有唯一的一个 space_id 作为标识。

**可以通过以下任一方法获取知识库的 space_id：**
- 调用 [获取知识空间列表](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/list)，从返回值中获取；
- 如果你是知识库管理员，可以进入知识库设置页面，复制地址栏的数字部分（见下图）：

![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/96ea466a484e8f3fdbfc8c2587b31750_ZpeqCy7xSe.png?height=620&lazyload=true&width=1240)

##  字段说明

名称 | 类型 | 描述
---|---|---
space_id | string | 一个知识空间的唯一标识。  <br>**示例值**："7034502641455497244"<br>**字段权限要求（任选其一）**：<br>查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly)
name | string | 知识空间的名称。
description | string | 知识空间的描述内容。
space_type | string | 表示知识空间类型<br>**可选值有**：<br>- `team`：团队空间，归团队（多人）管理，可添加多个管理员<br>- `person`：个人空间（旧版，已下线），归个人管理。一人仅可拥有一个，无法添加其他管理员<br>- `my_library`：我的文档库，归个人管理。一人仅可拥有一个，无法添加其他管理员

### 方法列表
>  “商店”代表 [应用商店应用](https://open.feishu.cn/document/home/app-types-introduction/overview)；“自建”代表 [企业自建应用](https://open.feishu.cn/document/home/app-types-introduction/overview)

**[方法 (API)](https://open.feishu.cn/document/ukTMukTMukTM/uITNz4iM1MjLyUzM)** | 权限要求（满足任一） | **[访问凭证](https://open.feishu.cn/document/ukTMukTMukTM/uMTNz4yM1MjLzUzM)（选择其一）** | 商店 | 自建
---|---|---|---|---
[创建知识空间](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/create)<br>`POST` /open-apis/wiki/v2/spaces | 查看、编辑和管理知识库(wiki:wiki) | `user_access_token` | **✓** | **✓**
[获取知识空间列表](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/list)<br>`GET` /open-apis/wiki/v2/spaces | 查看、编辑和管理知识库(wiki:wiki) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
[获取知识空间信息](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/get)<br>`GET` open-apis/wiki/v2/spaces/:space_id | 查看、编辑和管理知识库(wiki:wiki) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**

## 资源：知识空间成员 Member

知识空间具有权限管控，仅知识空间成员能访问该知识空间。

## 字段说明

名称 | 类型 | 描述
---|---|---
member_id | string | 一个知识空间成员的唯一标识。可以使用open_id, email等多种方法表示  <br>**示例值**："ou_51427140ab9f450411135757bcbf932f"<br>**字段权限要求（任选其一）**：<br>查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly)

### 方法列表
>  “商店”代表 [应用商店应用](https://open.feishu.cn/document/home/app-types-introduction/overview)；“自建”代表 [企业自建应用](https://open.feishu.cn/document/home/app-types-introduction/overview)

**[方法 (API)](https://open.feishu.cn/document/ukTMukTMukTM/uITNz4iM1MjLyUzM)** | 权限要求（满足任一） | **[访问凭证](https://open.feishu.cn/document/ukTMukTMukTM/uMTNz4yM1MjLzUzM)（选择其一）** | 商店 | 自建
---|---|---|---|---
[删除知识空间成员](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-member/delete)<br>`DELETE` /open-apis/wiki/v2/spaces/:space_id/members/:member_id | 查看、编辑和管理知识库(wiki:wiki) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
[添加知识空间成员](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-member/create)<br>`POST` /open-apis/wiki/v2/spaces/:space_id/members | 查看、编辑和管理知识库(wiki:wiki) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**

## 资源：知识空间设置 Setting

### 方法列表
>  “商店”代表 [应用商店应用](https://open.feishu.cn/document/home/app-types-introduction/overview)；“自建”代表 [企业自建应用](https://open.feishu.cn/document/home/app-types-introduction/overview)

**[方法 (API)](https://open.feishu.cn/document/ukTMukTMukTM/uITNz4iM1MjLyUzM)** | 权限要求（满足任一） | **[访问凭证](https://open.feishu.cn/document/ukTMukTMukTM/uMTNz4yM1MjLzUzM)（选择其一）** | 商店 | 自建
---|---|---|---|---
[更新知识空间设置](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-setting/update)<br>`PUT` /open-apis/wiki/v2/spaces/:space_id/setting | 查看、编辑和管理知识库(wiki:wiki) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**

## 资源：节点 Node
文件是各种类型的文件的统称，泛指云空间内所有的文件。每个文件都有唯一 token 作为标识。

##  字段说明

名称 | 类型 | 描述
---|---|---
node_token | string | 一个节点的唯一标识。  <br>**示例值**："wikcnpJLIzbAptN4cMQrQoewaLc"<br>**字段权限要求（任选其一）**：<br>查看、编辑和管理知识库(wiki:wiki)
obj_token | string | 节点的真实文档的 token，如果要获取或编辑节点内容，需要使用此 token 调用对应的接口。
obj_type | string | 节点的类型，可能是 doc、sheet、bitable、file、folder 中的一种。

### 方法列表
>  “商店”代表 [应用商店应用](https://open.feishu.cn/document/home/app-types-introduction/overview)；“自建”代表 [企业自建应用](https://open.feishu.cn/document/home/app-types-introduction/overview)

**[方法 (API)](https://open.feishu.cn/document/ukTMukTMukTM/uITNz4iM1MjLyUzM)** | 权限要求（满足任一） | **[访问凭证](https://open.feishu.cn/document/ukTMukTMukTM/uMTNz4yM1MjLzUzM)（选择其一）** | 商店 | 自建
---|---|---|---|---
[创建节点](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-node/create)<br>`POST` /open-apis/wiki/v2/spaces/:space_id/nodes | 查看、编辑和管理知识库(wiki:wiki) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
[获取子节点列表](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-node/list)<br>`GET` /open-apis/wiki/v2/spaces/:space_id/nodes | 查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
[获取节点信息](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/get_node)<br>`GET` /open-apis/wiki/v2/spaces/get_node | 查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
[添加已有云文档至知识库](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-node/move_docs_to_wiki)<br>`POST` /open-apis/wiki/v2/spaces/:space_id/nodes/move_docs_to_wiki | 查看、编辑和管理知识库(wiki:wiki) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**
[知识空间内移动节点](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-node/move)<br>`POST` /open-apis/wiki/v2/spaces/:space_id/nodes/:node_token/move | 查看、编辑和管理知识库(wiki:wiki) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**

## 资源：任务 Task
对于耗时比较长的操作，例如[添加已有云文档至知识库](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-node/move_docs_to_wiki)，会以异步任务来表示。

## 字段说明

名称 | 类型 | 描述
---|---|---
task_id | string | 一个知识空间的唯一标识。  <br>**示例值**："7078885194417045524-8316a3d38e2ef0e7c69149d3db4590ec031d9cbc"<br>**字段权限要求（任选其一）**：<br>查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly)

### 方法列表
>  “商店”代表 [应用商店应用](https://open.feishu.cn/document/home/app-types-introduction/overview)；“自建”代表 [企业自建应用](https://open.feishu.cn/document/home/app-types-introduction/overview)

**[方法 (API)](https://open.feishu.cn/document/ukTMukTMukTM/uITNz4iM1MjLyUzM)** | 权限要求（满足任一） | **[访问凭证](https://open.feishu.cn/document/ukTMukTMukTM/uMTNz4yM1MjLzUzM)（选择其一）** | 商店 | 自建
---|---|---|---|---
[获取任务结果](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/task/get)<br>`GET` /open-apis/wiki/v2/tasks/:task_id | 查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly) | `tenant_access_token`<br>`user_access_token` | **✓** | **✓**

## 权限说明

知识空间具有灵活的权限管控，以下描述通常涉及的权限点位。接口具体权限要求请查看接口文档**知识库权限要求**。

### 节点阅读权限

允许查看节点/文档。

拥有编辑权限时自动拥有阅读权限。

### 容器编辑权限

允许编辑文档。允许添加/删除子节点。

知识空间管理员拥有所有节点的容器编辑权限，且不可移除。

### 单页面编辑权限

允许编辑文档。但不允许添加/删除子节点。

### 知识空间成员默认权限

知识空间成员默认权限为阅读权限，可以在知识空间设置页修改。

### 应用/机器人如何获得权限

有两种途径：添加为知识空间成员/管理员 或 添加为文档协作者。

1. [添加为知识空间成员/管理员](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#b5da330b)。
2. [添加为文档协作者](https://open.feishu.cn/document/ukTMukTMukTM/uIzNzUjLyczM14iM3MTN/faq#40c028dd)。

# 知识库常见问题

## 1. 如何调用接口获取知识库文档内容 / 如何调用接口操作知识库文档？

要获取知识库中云文档的内容/调用接口操作知识库文档，你需先通过知识库相关接口获取该云文档资源的实际 token，再调用云文档资源相关获取接口。具体步骤如下所示：<br>1. 在 URL 地址栏，获取知识库中云文档挂载的节点标识 `node_token`。如下图，该文档挂载的节点 token 为 `EpMmw5WZQi7tYRk73gBc7Dabcef`。<br>你也可通过[获取知识空间列表](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/list)获取知识空间的标识 `space_id`，再通过[获取知识空间子节点列表](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-node/list)获取云文档挂载的节点 `node_token`。<br>![](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/9a4195d235cb581c5a644278c872a73e_kDDonAPndG.png?height=935&lazyload=true&maxWidth=500&width=1573)<br>1. 通过[获取知识空间节点信息](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/get_node)接口，获取该节点下挂载的云资源的 **obj_token**。此时，该 **obj_token** 即为云文档资源的实际 token。<br>1. 根据云文档类型，使用[文档](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-overview)、[电子表格](https://open.feishu.cn/document/ukTMukTMukTM/uATMzUjLwEzM14CMxMTN/overview)、[多维表格](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/bitable-overview)等接口获取内容：<br>1. 如果该云文档类型为文档，你可调用[获取文档纯文本内容](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document/raw_content)或[获取文档所有块](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-v1/document-block/list)获取文档内容<br>1. 如果该云文档类型为电子表格，你可调用[读取多个范围](https://open.feishu.cn/document/ukTMukTMukTM/ukTMzUjL5EzM14SOxMTN)等接口获取电子表格中的数据<br>1. 如果该云文档类型为多维表格，你可调用[查询记录](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/bitable-v1/app-table-record/search)等接口获取多维表格中的记录数据<br>**说明**：<br>知识库中的云文档的特殊之处在于，云文档 URL 地址中的 token 为知识库的节点标识（node_token），而不是实际云文档资源的唯一标识。例如，在 URL `https://sample.feishu.cn/wiki/EpMmw5WZQi7tYRk73gBc7Dabcef` 中，`EpMmw5WZQi7tYRk73gBc7Dabcef` 为知识库的节点 token，而不是[文档](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/document-docx/docx-overview)的唯一标识 `document_id`。
---

## 2. 如何给应用授权访问知识库文档资源？

知识库 API 中，除了 [创建知识库](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/create) 和[搜索Wiki](https://open.feishu.cn/document/ukTMukTMukTM/uEzN0YjLxcDN24SM3QjN/search_wiki)以外，都支持使用 **tenant_access_token** 进行调用。<br>应用在访问知识库之前需要获得知识库管理员的授权，或者某个节点的访问权限。要为应用授权整个知识库的访问权限，参考以下步骤：<br>- 方式一：添加群为知识库管理员或成员<br>1. 访问[开发者后台](https://open.feishu.cn/app)，选择目标应用。<br>1. 在应用管理页面，点击**添加应用能力**，找到机器人卡片，点击 **+添加**。<br>![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/ca6dc6a875f0de5ab6dd5f37dd1c6c16_nQvJbqJSSb.png?height=1376&lazyload=true&maxWidth=728&width=2686)<br>3. 发布当前应用版本，并确保发布版本的[可用范围](https://open.feishu.cn/document/home/introduction-to-scope-and-authorization/availability)包含文件夹资源的所有者。<br>4. 在飞书客户端，创建一个新的群组，将应用添加为群机器人。warning<br>**注意**<br>此处要添加应用作为机器人，而不是添加“自定义机器人”。<br>5. 知识库管理员前往「**知识库设置**」-> 「**成员设置**」，在此选择添加的角色：管理员、可编辑的成员或可阅读的成员。<br>![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/f2d8f0e7168dc1a7d9e4e7264ff2af51_XFAHwdOfD3.png?height=878&lazyload=true&maxWidth=728&width=1920)<br>6. 搜索包含机器人的群聊，添加该群为管理员或成员。<br>![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/dae728569130e1ca3438e931769e92a2_0S52GbbvjE.png?height=838&lazyload=true&maxWidth=528&width=1135)<br>- 方式二：通过 API 接口将应用添加为知识库管理员或成员<br>1. 获得知识库管理员身份凭证（user_access_token）。<br>2. 获取应用 **open_id**（参考[云文档常见问题](https://open.feishu.cn/document/ukTMukTMukTM/uczNzUjL3czM14yN3MTN) **问题 10 如何获取应用 open_id？**）。<br>3. 调用[添加为知识空间成员](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-member/create)接口，通过管理员身份（user_access_token）将应用 **open_id** 添加为知识空间成员。通过 `member_role` 参数控制角色类型。<br>要为应用授权知识库中部分内容的访问权限，你可将应用添加为知识库中目标节点云文档的协作者，应用将拥有该节点下所有云文档的协作权限。具体步骤如下所示：<br>- 方式一：直接添加应用为节点云文档的协作者<br>该方式要求操作者为云文档所有者、拥有文档**管理**权限的协作者或知识库管理员。操作者可通过云文档网页页面右上方「**...**」->「**...更多**」-> 「**添加文档应用**」入口添加。<br>![](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/22c027f63c540592d3ca8f41d48bb107_CSas7OYJBR.png?height=1994&lazyload=true&maxWidth=583&width=3278)<br>- 方式二：添加包含应用的群组为节点云文档的协作者<br>1.  访问[开发者后台](https://open.feishu.cn/app)，选择目标应用。<br>1. 在应用管理页面，点击**添加应用能力**，找到机器人卡片，点击 **+添加**。<br>2. 发布当前应用版本，并确保发布版本的[可用范围](https://open.feishu.cn/document/home/introduction-to-scope-and-authorization/availability)包含知识库资源的所有者。<br>3. 在飞书客户端，创建一个新的群组，将应用添加为群机器人。warning<br>**注意**<br>此处要添加应用作为机器人，而不是添加“自定义机器人”。<br>2. 在目标节点，将该节点分享给刚刚新建的群组，并设置权限。<br>![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/6a32d4b28f31b942e92b7f8dd9bed33c_eCrlCr1vtb.png?height=875&lazyload=true&maxWidth=728&width=1903)<br>- 方式三：通过用户身份凭证 (user_access_token) 调用[增加协作者权限](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/permission-member/create)通过应用的 open_id（参考[云文档常见问题](https://open.feishu.cn/document/ukTMukTMukTM/uczNzUjL3czM14yN3MTN)问题 10 “如何获取应用 open_id ”） 给应用授予文档的访问权限。<br>- 方式四：通过用户身份凭证(user_access_token) 调用[更新云文档权限设置](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/permission-public/patch)，将权限设置为“组织内获得链接的人可编辑”。<br>- 方式五：通过用户身份凭证(user_access_token) 调用[转移所有者](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/permission-member/transfer_owner)将云文档的所有权转移给应用。
---

## 3. 如何将应用添加为知识库管理员（成员）？

添加应用为知识库管理员（成员）当前有两种方式：<br>- 通过添加群为知识库管理员（成员）方式（**较容易**）<br>1. 在飞书客户端中创建一个群聊，并将应用添加至群聊中。<br>2. 知识库管理员前往「**知识库设置**」-> 「**成员设置**」->「**添加管理员**」中。<br>![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/f2d8f0e7168dc1a7d9e4e7264ff2af51_XFAHwdOfD3.png?height=878&lazyload=true&maxWidth=483&width=1920)<br>3. 搜索包含机器人的群聊，添加该群为管理员。<br>![image.png](//sf3-cn.feishucdn.com/obj/open-platform-opendoc/dae728569130e1ca3438e931769e92a2_0S52GbbvjE.png?height=838&lazyload=true&maxWidth=483&width=1135)<br>- 通过 API 接口方式(**较繁琐**)<br>- 参考本页 **问题2 中将应用添加知识空间成员的方式**
---

## 4. 如何迁移云空间中的文档到知识库？

1. 确定当前使用访问凭证是 **user_access_token** 还是 **tenant_access_token**。<br>2. 确认当前身份是否是迁移文档的所有者。<br>3. 确认当前身份是否拥有知识库迁移目的地节点的权限。参考本页 **问题2**。<br>4. 调用 [添加已有云文档至知识库<br>](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space-node/move_docs_to_wiki)接口进行迁移。<br>- 此接口为异步接口。若移动已完成（或节点已在Wiki中），则直接返回结果（Wiki token）。<br>- 若尚未完成，则返回task id。请使用[获取任务结果](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/task/get)接口进行查询。
---

## 5. 如何将本地文件导入到知识库？

1. 先将本地文件通过[导入流程](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/import_task/import-user-guide)导入到云空间。<br>2. 再通过本页**问题4 如何迁移云空间中的文档到知识库** 将导入后的文档迁移到知识库中。
---

## 6. 如何导出知识库中文档？

1. 通过调用 [获取节点信息](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/get_node) 接口，可以从返回值中获取到 `obj_type` 和 `obj_token`。<br>2. 再通过[导出流程](https://open.feishu.cn/document/uAjLw4CM/ukTMukTMukTM/reference/drive-v1/export_task/export-user-guide)将`obj_token`对应的文档下载到本地。
---

## 7. 如何查看谁是当前知识库的管理员？

你可前往飞书帮助中心[知识库管理员常见问题](https://www.feishu.cn/hc/zh-CN/articles/573667449126-%E7%9F%A5%E8%AF%86%E5%BA%93%E7%AE%A1%E7%90%86%E5%91%98%E5%B8%B8%E8%A7%81%E9%97%AE%E9%A2%98#tabs0|lineguid-Mqjr1)了解。
---

# 获取知识空间列表

此接口用于获取有权限访问的知识空间列表。

## 注意事项

- 使用 tenant access token 调用时，请确认应用或机器人拥有部分知识空间的访问权限，否则返回列表为空。参阅[如何将应用添加为知识库管理员（成员）](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#b5da330b)。
- 此接口为分页接口。由于权限过滤，可能返回列表为空，但当分页标记（has_more）为 true 时，可以继续分页请求。
- 此接口不会返回**我的文档库**。

## 请求

基本 | &nbsp;
---|---
HTTP URL | https://open.feishu.cn/open-apis/wiki/v2/spaces
HTTP Method | GET
接口频率限制 | [100 次/分钟](https://open.feishu.cn/document/ukTMukTMukTM/uUzN04SN3QjL1cDN)
支持的应用类型 | Custom App、Store App
权限要求<br>**调用该 API 所需的权限。开启其中任意一项权限即可调用**<br>开启任一权限即可 | 查看知识空间列表(wiki:space:retrieve)<br>查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly)

### 请求头

名称 | 类型 | 必填 | 描述
---|---|---|---
Authorization | string | 是 | `tenant_access_token`<br>或<br>`user_access_token`<br>**值格式**："Bearer `access_token`"<br>**示例值**："Bearer u-7f1bcd13fc57d46bac21793a18e560"<br>[了解更多：如何选择与获取 access token](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-choose-which-type-of-token-to-use)

### 查询参数

名称 | 类型 | 必填 | 描述
---|---|---|---
page_size | int | 否 | 分页大小<br>**示例值**：10<br>**默认值**：`20`<br>**数据校验规则**：<br>- 最大值：`50`
page_token | string | 否 | 分页标记，第一次请求不填，表示从头开始遍历；分页查询结果还有更多项时会同时返回新的 page_token，下次遍历可采用该 page_token 获取查询结果<br>**示例值**：1565676577122621

## 响应

### 响应体

名称 | 类型 | 描述
---|---|---
code | int | 错误码，非 0 表示失败
msg | string | 错误描述
data | \- | \-
items | space\[\] | 数据列表
name | string | 知识空间名称
description | string | 知识空间描述
space_id | string | 知识空间 ID
space_type | string | 表示知识空间类型<br>**可选值有**：<br>- team：团队空间，归团队（多人）管理，可添加多个管理员<br>- person：个人空间（旧版，已下线），归个人管理。一人仅可拥有一个，无法添加其他管理员<br>- my_library：我的文档库，归个人管理。一人仅可拥有一个，无法添加其他管理员
visibility | string | 表示知识空间可见性<br>**可选值有**：<br>- public：公开空间，租户内所有用户可见，默认为成员权限。无法额外添加成员，但可以添加管理员<br>- private：私有空间，仅对知识空间管理员、成员可见，需要手动添加管理员、成员
open_sharing | string | 表示知识空间的分享状态<br>**可选值有**：<br>- open：打开，即知识空间发布到互联网<br>- closed：关闭，即知识空间未发布到互联网
page_token | string | 分页标记，当 has_more 为 true 时，会同时返回新的 page_token，否则不返回 page_token
has_more | boolean | 是否还有更多项

### 响应体示例
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "items": [
            {
                "name": "知识空间",
                "description": "知识空间描述",
                "space_id": "1565676577122621"
            }
        ],
        "page_token": "1565676577122621",
        "has_more": true
    }
}
```

### 错误码

HTTP状态码 | 错误码 | 描述 | 排查建议
---|---|---|---
400 | 131001 | rpc fail | 服务报错（下游 RPC 调用失败），请稍后重试，或者拿响应体的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131002 | param err | 通常为传参有误，例如数据类型不匹配。请查看响应体 msg 字段中的具体接口报错信息，报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131004 | invalid user | 非法用户（如未登陆或用户 ID 校验失败）。请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131007 | internal err | 服务内部错误，请勿重试，拿返回值的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。

# 获取知识空间信息

此接口用于根据知识空间 ID 查询知识空间的信息，包括空间的类型、可见性、分享状态等。

## 前提条件

调用此接口前，请确保应用或用户为知识空间的成员或管理员。

## 请求

基本 | &nbsp;
---|---
HTTP URL | https://open.feishu.cn/open-apis/wiki/v2/spaces/:space_id
HTTP Method | GET
接口频率限制 | [100 次/分钟](https://open.feishu.cn/document/ukTMukTMukTM/uUzN04SN3QjL1cDN)
支持的应用类型 | Custom App、Store App
权限要求<br>**调用该 API 所需的权限。开启其中任意一项权限即可调用**<br>开启任一权限即可 | 查看知识空间信息(wiki:space:read)<br>查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly)

### 请求头

名称 | 类型 | 必填 | 描述
---|---|---|---
Authorization | string | 是 | `tenant_access_token`<br>或<br>`user_access_token`<br>**值格式**："Bearer `access_token`"<br>**示例值**："Bearer u-7f1bcd13fc57d46bac21793a18e560"<br>[了解更多：如何选择与获取 access token](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-choose-which-type-of-token-to-use)

### 路径参数

名称 | 类型 | 描述
---|---|---
space_id | string | 知识空间 ID。可通过以下两种方式获取。了解更多，参考[知识库概述](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-overview)。<br>- 调用 [获取知识空间列表](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/space/list)获取<br>- 如果你是知识库管理员，可以进入知识库设置页面，复制地址栏的数字部分：https://sample.feishu.cn/wiki/settings/==6870403571079249922==<br>**示例值**："6870403571079249922"

### 查询参数

名称 | 类型 | 必填 | 描述
---|---|---|---
lang | string | 否 | 当查询**我的文档库**时，指定返回的文档库名称展示语言。<br>**示例值**：zh<br>**可选值有**：<br>- zh：简体中文<br>- id：印尼语<br>- de：德语<br>- en：英语<br>- es：西班牙语<br>- fr：法语<br>- it：意大利语<br>- pt：葡萄牙语<br>- vi：越南语<br>- ru：俄语<br>- hi：印地语<br>- th：泰语<br>- ko：韩语<br>- ja：日语<br>- zh-HK：繁体中文（中国香港）<br>- zh-TW：繁体中文（中国台湾）<br>**默认值**：`en`

## 响应

### 响应体

名称 | 类型 | 描述
---|---|---
code | int | 错误码，非 0 表示失败
msg | string | 错误描述
data | \- | \-
space | space | 知识空间
name | string | 知识空间名称
description | string | 知识空间描述
space_id | string | 知识空间 ID
space_type | string | 表示知识空间类型<br>**可选值有**：<br>- team：团队空间，归团队（多人）管理，可添加多个管理员<br>- person：个人空间（旧版，已下线），归个人管理。一人仅可拥有一个，无法添加其他管理员<br>- my_library：我的文档库，归个人管理。一人仅可拥有一个，无法添加其他管理员
visibility | string | 表示知识空间可见性<br>**可选值有**：<br>- public：公开空间。租户所有用户可见，默认为成员权限。无法额外添加成员，但可以添加管理员<br>- private：私有空间。仅对知识空间管理员、成员可见，需要手动添加管理员、成员
open_sharing | string | 表示知识空间的分享状态<br>**可选值有**：<br>- open：打开，即知识空间发布到互联网<br>- closed：关闭，即知识空间未发布到互联网

### 响应体示例
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "space": {
            "name": "知识空间",
            "description": "知识空间描述",
            "space_id": "1565676577122621"
        }
    }
}
```

### 错误码

HTTP状态码 | 错误码 | 描述 | 排查建议
---|---|---|---
400 | 131001 | rpc fail | 服务报错（下游 RPC 调用失败），请稍后重试，或者拿响应体的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131002 | param err | 通常为传参有误，例如数据类型不匹配。请查看响应体 msg 字段中的具体接口报错信息，报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131004 | invalid user | 非法用户（如未登陆或用户 ID 校验失败）。请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131005 | not found | 未找到相关数据，例如id不存在。相关报错信息参考：<br>- member not found：用户不是知识空间成员（管理员），无法删除。<br>- identity not found: userid不存在，无法添加/删除成员。<br>- space not found：知识空间不存在<br>- node not found：节点不存在<br>- document not found：文档不存在<br>报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131006 | permission denied | 权限拒绝，相关报错信息参考：<br>- wiki space permission denied：知识库权限鉴权不通过，需要成为知识空间管理员（成员）。<br>- node permission denied：文档节点权限鉴权不通过，读操作需要具备节点阅读权限，写操作（创建、移动等）则需要具备节点容器编辑权限。<br>- no source parent node permission：需要具备原父节点的容器编辑权限。<br>- no destination parent node permission：需要具备目标父节点的容器编辑权限，若移动到知识空间下，则需要成为知识空间管理员（成员）。<br>**注意**：应用访问或操作文档时，除了申请 API 权限，还需授权具体文档资源的阅读、编辑或管理权限。<br>请参考以下步骤操作： <br>1. **当遇到资源权限不足的情况**：参阅[如何给应用授权访问知识库文档资源](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#a40ad4ca)。<br>2. **也可直接将应用添加为知识库管理员（成员）**：参阅[如何将应用添加为知识库管理员（成员）](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#b5da330b)。<br>3. **若无法解决或报错信息不明确时**：请咨询[技术支持](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131007 | internal err | 服务内部错误，请勿重试，拿返回值的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。

# 创建知识空间节点

此接口用于在知识节点里创建[节点](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-overview)到指定位置。

**注意事项**：- 知识空间权限要求，当前使用的 access token 所代表的应用或用户拥有：
  - **父节点**容器编辑权限

- 当前不支持创建`文件`类型节点。

## 请求

基本 | &nbsp;
---|---
HTTP URL | https://open.feishu.cn/open-apis/wiki/v2/spaces/:space_id/nodes
HTTP Method | POST
接口频率限制 | [100 次/分钟](https://open.feishu.cn/document/ukTMukTMukTM/uUzN04SN3QjL1cDN)
支持的应用类型 | Custom App、Store App
权限要求<br>**调用该 API 所需的权限。开启其中任意一项权限即可调用**<br>开启任一权限即可 | 创建知识空间节点(wiki:node:create)<br>查看、编辑和管理知识库(wiki:wiki)

### 请求头

名称 | 类型 | 必填 | 描述
---|---|---|---
Authorization | string | 是 | `tenant_access_token`<br>或<br>`user_access_token`<br>**值格式**："Bearer `access_token`"<br>**示例值**："Bearer u-7f1bcd13fc57d46bac21793a18e560"<br>[了解更多：如何选择与获取 access token](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-choose-which-type-of-token-to-use)
Content-Type | string | 是 | **固定值**："application/json; charset=utf-8"

### 路径参数

名称 | 类型 | 描述
---|---|---
space_id | string | 知识空间id<br>[获取方式](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-overview)<br>**示例值**："6704147935988285963"

### 请求体

名称 | 类型 | 必填 | 描述
---|---|---|---
obj_type | string | 是 | 文档类型，对于快捷方式，该字段是对应的实体的obj_type。<br>**示例值**："docx"<br>**可选值有**：<br>- doc：已废弃，创建文档请使用`docx`。详情参考[旧版文档（Docs 1.0）创建能力下线说明](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/breaking-change/docs-create-ability-offline)。<br>- sheet：表格<br>- mindnote：思维导图<br>- bitable：多维表格<br>- file：文件<br>- docx：新版文档<br>- slides：幻灯片
parent_node_token | string | 否 | 父节点 token。若当前节点为一级节点，父节点 token 为空。<br>**示例值**："wikcnKQ1k3p******8Vabcef"
node_type | string | 是 | 节点类型<br>**示例值**："origin"<br>**可选值有**：<br>- origin：实体<br>- shortcut：快捷方式
origin_node_token | string | 否 | 快捷方式对应的实体node_token，当节点为快捷方式时，该值不为空。<br>**示例值**："wikcnKQ1k3p******8Vabcef"
title | string | 否 | 文档标题<br>**示例值**："标题"

### 请求体示例
```json
// 创建文档为某文档子节点：
{
    "obj_type": "docx",
    "parent_node_token": "wikcnKQ1k3p******8Vabcef",
    "node_type": "origin"
}

// 创建文档为空间一级节点：
{
    "obj_type": "docx",
    "node_type": "origin"
}

// 创建某一知识空间文档的快捷方式为文档子节点：
{
    "obj_type": "docx",
    "parent_node_token": "wikcnKQ1k3p******8Vabcef",
    "node_type": "shortcut"，
    "origin_node_token": "wikcnKQ1k3p******8Vabcef"
}
```

## 响应

### 响应体

名称 | 类型 | 描述
---|---|---
code | int | 错误码，非 0 表示失败
msg | string | 错误描述
data | \- | \-
node | node | 节点
space_id | string | 知识空间id<br>[获取方式](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-overview)
node_token | string | 节点token
obj_token | string | 对应文档类型的token，可根据 obj_type 判断属于哪种文档类型。
obj_type | string | 文档类型，对于快捷方式，该字段是对应的实体的obj_type。<br>**可选值有**：<br>- doc：旧版文档<br>- sheet：表格<br>- mindnote：思维导图<br>- bitable：多维表格<br>- file：文件<br>- docx：新版文档<br>- slides：幻灯片
parent_node_token | string | 父节点 token。若当前节点为一级节点，父节点 token 为空。
node_type | string | 节点类型<br>**可选值有**：<br>- origin：实体<br>- shortcut：快捷方式
origin_node_token | string | 快捷方式对应的实体node_token，当节点为快捷方式时，该值不为空。
origin_space_id | string | 快捷方式对应的实体所在的space id
has_child | boolean | 是否有子节点
title | string | 文档标题
obj_create_time | string | 文档创建时间
obj_edit_time | string | 文档最近编辑时间
node_create_time | string | 节点创建时间
creator | string | 节点创建者
owner | string | 节点所有者
node_creator | string | 节点创建者

### 响应体示例
```json
// 实体节点
{
    "code": 0,
    "msg": "success",
    "data": {
        "node": {
            "space_id": "6946843325487906839",
            "node_token": "wikcnKQ1k3p******8Vabcef",
            "obj_token": "doccnzAaO******8g9Spprd",
            "obj_type": "doc",
            "parent_node_token": "wikcnKQ1k3p******8Vabcef",
            "node_type": "origin",
            "origin_node_token": "",
            "origin_space_id": "",
            "has_child": false,
            "title": ""
        }
    }
}

// 快捷方式节点
{
    "code": 0,
    "msg": "success",
    "data": {
        "node": {
            "space_id": "6946843325487906839",
            "node_token": "wikcnKQ1k3p******8Vabcef",
            "obj_token": "doccnzAaO******8g9Spprd",
            "obj_type": "doc",
            "parent_node_token": "wikcnKQ1k3p******8Vabcef",
            "node_type": "shortcut",
            "origin_node_token": "wikcnKQ1k3p******8Vabcef",
            "origin_space_id": "6946843325487906839",
            "has_child": false,
            "title": ""
        }
    }
}
```

### 错误码

HTTP状态码 | 错误码 | 描述 | 排查建议
---|---|---|---
400 | 131001 | rpc fail | 服务报错，请稍后重试，或者拿响应体的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131002 | param err | 通常为传参有误，例如数据类型不匹配。请查看**具体接口报错信息**，报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131003 | out of limit | 超出操作限制，例如节点数量限制。请参阅下表。<br>- 原/目标知识空间总节点数不超过40万。<br>- 原/目标知识空间目录树不超过50层。<br>- 目的父节点下单层节点数不超过2000。<br>- 单次移动节点数（带子节点）不超过2000。
400 | 131004 | invalid user | 非法用户。请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131005 | not found | 未找到相关数据，例如id不存在。相关报错信息参考：<br>- member not found：用户不是知识空间成员（管理员），无法删除。<br>- identity not found: userid不存在，无法添加/删除成员。<br>- space not found：知识空间不存在<br>- node not found：节点不存在<br>- document not found：文档不存在<br>报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131006 | permission denied | 权限拒绝，相关报错信息参考：<br>- wiki space permission denied：知识库权限鉴权不通过，需要成为知识空间管理员（成员）。<br>- node permission denied：文档节点权限鉴权不通过，读操作需要具备节点阅读权限，写操作（创建、移动等）则需要具备节点容器编辑权限。<br>- no source parent node permission：需要具备原父节点的容器编辑权限。<br>- no destination parent node permission：需要具备目标父节点的容器编辑权限，若移动到知识空间下，则需要成为知识空间管理员（成员）。<br>**注意**：应用访问或操作文档时，除了申请 API 权限，还需授权具体文档资源的阅读、编辑或管理权限。<br>请参考以下步骤操作： <br>1. **当遇到资源权限不足的情况**：参阅[如何给应用授权访问知识库文档资源](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#a40ad4ca)。<br>2. **也可直接将应用添加为知识库管理员（成员）**：参阅[如何将应用添加为知识库管理员（成员）](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#b5da330b)。<br>3. **若无法解决或报错信息不明确时**：请咨询[技术支持](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131007 | internal err | 服务内部错误，请勿重试，拿返回值的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131009 | lock contention, please retry later. | 并发请求异常，请稍后重试。
400 | 131010 | doc type is deprecated, please use docx. | 旧版文档创建能力已下线，详情参考[旧版文档（Docs 1.0）创建能力下线说明](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/breaking-change/docs-create-ability-offline)。

# 获取知识空间节点信息

获取知识空间节点信息

**注意事项**：知识库权限要求，当前使用的 access token 所代表的应用或用户拥有：
- 节点阅读权限

## 请求

基本 | &nbsp;
---|---
HTTP URL | https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node
HTTP Method | GET
接口频率限制 | [100 次/分钟](https://open.feishu.cn/document/ukTMukTMukTM/uUzN04SN3QjL1cDN)
支持的应用类型 | Custom App、Store App
权限要求<br>**调用该 API 所需的权限。开启其中任意一项权限即可调用**<br>开启任一权限即可 | 查看知识空间节点信息(wiki:node:read)<br>查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly)

### 请求头

名称 | 类型 | 必填 | 描述
---|---|---|---
Authorization | string | 是 | `tenant_access_token`<br>或<br>`user_access_token`<br>**值格式**："Bearer `access_token`"<br>**示例值**："Bearer u-7f1bcd13fc57d46bac21793a18e560"<br>[了解更多：如何选择与获取 access token](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-choose-which-type-of-token-to-use)

### 查询参数

名称 | 类型 | 必填 | 描述
---|---|---|---
token | string | 是 | 知识库节点或对应云文档的实际 token。<br>- 知识库节点 token：如果 URL 链接中 token 前为 wiki，该 token 为知识库的节点 token。<br>- 云文档实际 token：如果 URL 链接中 token 前为 docx、base、sheets 等非 wiki 类型，则说明该 token 是当前云文档的实际 token。<br>了解更多，请参考[文档常见问题-如何获取云文档资源相关 token（id）](https://open.feishu.cn/document/ukTMukTMukTM/uczNzUjL3czM14yN3MTN)。<br>**注意**：<br>使用云文档 token 查询时，需要对 obj_type 参数传入文档对应的类型。<br>**示例值**：wikcnKQ1k3p******8Vabcef<br>**数据校验规则**：<br>- 长度范围：`0` ～ `999` 字符
obj_type | string | 否 | 文档类型。不传时默认以 wiki 类型查询。<br>**示例值**：docx<br>**可选值有**：<br>- doc：旧版文档<br>- docx：新版文档<br>- sheet：表格<br>- mindnote：思维导图<br>- bitable：多维表格<br>- file：文件<br>- slides：幻灯片<br>- wiki：知识库节点<br>**默认值**：`wiki`

## 响应

### 响应体

名称 | 类型 | 描述
---|---|---
code | int | 错误码，非 0 表示失败
msg | string | 错误描述
data | \- | \-
node | node | 节点信息
space_id | string | 知识空间 ID。获取方式参考[知识库概述](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-overview)。
node_token | string | 知识库节点 token，如果 URL 链接中 token 前为 wiki，该 token 为知识库的节点 token。
obj_token | string | 节点的实际云文档的 token，如果 URL 链接中 token 前为 docx、base、sheets 等非 wiki 类型，则说明该 token 是当前云文档的实际 token。如果要获取或编辑节点内容，需要使用此 token 调用对应的接口。可根据 obj_type 判断属于哪种文档类型。
obj_type | string | 文档类型，对于快捷方式，该字段是对应的实体的obj_type。<br>**可选值有**：<br>- doc：旧版文档<br>- sheet：表格<br>- mindnote：思维导图<br>- bitable：多维表格<br>- file：文件<br>- docx：新版文档<br>- slides：幻灯片
parent_node_token | string | 父节点 token。若当前节点为一级节点，父节点 token 为空。
node_type | string | 节点类型<br>**可选值有**：<br>- origin：实体<br>- shortcut：快捷方式
origin_node_token | string | 快捷方式对应的实体node_token，当节点为快捷方式时，该值不为空。
origin_space_id | string | 快捷方式对应的实体所在的space id
has_child | boolean | 是否有子节点
title | string | 文档标题
obj_create_time | string | 文档创建时间
obj_edit_time | string | 文档最近编辑时间
node_create_time | string | 节点创建时间
creator | string | 文档创建者
owner | string | 文档所有者
node_creator | string | 节点创建者

### 响应体示例
```json
// 使用Wiki Token查询：GET open-apis/wiki/v2/spaces/get_node?token=wikcnKQ1k3p******8Vabcef
// 或使用文档Token查询：GET open-apis/wiki/v2/spaces/get_node?token=doccnzAaOD******Wabcdef&obj_type=doc
{
    "code": 0,
    "msg": "success",
    "data": {
        "node": {
            "space_id": "6946843325487912356",
            "node_token": "wikcnKQ1k3p******8Vabcef",
            "obj_token": "doccnzAaOD******Wabcdef",
            "obj_type": "doc",
            "parent_node_token": "wikcnKQ1k3p******8Vabcef",
            "node_type": "origin",
            "origin_node_token": "wikcnKQ1k3p******8Vabcef",
            "origin_space_id": "6946843325487912356",
            "has_child": false,
            "title": "标题",
            "obj_create_time": "1642402428",
            "obj_edit_time": "1642402428",
            "node_create_time": "1642402428",
            "creator": "ou_xxxxx",
            "owner": "ou_xxxxx",
            "node_creator": "ou_xxxxx",
        }
    }
}
```

### 错误码

HTTP状态码 | 错误码 | 描述 | 排查建议
---|---|---|---
400 | 131001 | rpc fail | 服务报错，请稍后重试，或者拿响应体的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131002 | param err | 通常为传参有误，例如数据类型不匹配。请查看**具体接口报错信息**，报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131004 | invalid user | 非法用户。请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131005 | not found | 未找到相关数据，例如id不存在。相关报错信息参考：<br>- member not found：用户不是知识空间成员（管理员），无法删除。<br>- identity not found: userid不存在，无法添加/删除成员。<br>- space not found：知识空间不存在<br>- node not found：节点不存在<br>- document not found：文档不存在<br>- document is not in wiki：文档不在知识库中<br>报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131006 | permission denied | 权限拒绝，相关报错信息参考：<br>- wiki space permission denied：知识库权限鉴权不通过，需要成为知识空间管理员（成员）。<br>- node permission denied：文档节点权限鉴权不通过，读操作需要具备节点阅读权限，写操作（创建、移动等）则需要具备节点容器编辑权限。<br>- no source parent node permission：需要具备原父节点的容器编辑权限。<br>- no destination parent node permission：需要具备目标父节点的容器编辑权限，若移动到知识空间下，则需要成为知识空间管理员（成员）。<br>**注意**：应用访问或操作文档时，除了申请 API 权限，还需授权具体文档资源的阅读、编辑或管理权限。<br>请参考以下步骤操作： <br>1. **当遇到资源权限不足的情况**：参阅[如何给应用授权访问知识库文档资源](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#a40ad4ca)。<br>2. **也可直接将应用添加为知识库管理员（成员）**：参阅[如何将应用添加为知识库管理员（成员）](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#b5da330b)。<br>3. **若无法解决或报错信息不明确时**：请咨询[技术支持](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131007 | internal err | 服务内部错误，请勿重试，拿返回值的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。

# 获取知识空间子节点列表

此接口用于分页获取Wiki节点的子节点列表。

此接口为分页接口。由于权限过滤，可能返回列表为空，但分页标记（has_more）为true，可以继续分页请求。

**注意事项**：知识库权限要求，当前使用的 access token 所代表的应用或用户拥有：
- 父节点阅读权限

## 请求

基本 | &nbsp;
---|---
HTTP URL | https://open.feishu.cn/open-apis/wiki/v2/spaces/:space_id/nodes
HTTP Method | GET
接口频率限制 | [100 次/分钟](https://open.feishu.cn/document/ukTMukTMukTM/uUzN04SN3QjL1cDN)
支持的应用类型 | Custom App、Store App
权限要求<br>**调用该 API 所需的权限。开启其中任意一项权限即可调用**<br>开启任一权限即可 | 查看知识空间节点列表(wiki:node:retrieve)<br>查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly)

### 请求头

名称 | 类型 | 必填 | 描述
---|---|---|---
Authorization | string | 是 | `tenant_access_token`<br>或<br>`user_access_token`<br>**值格式**："Bearer `access_token`"<br>**示例值**："Bearer u-7f1bcd13fc57d46bac21793a18e560"<br>[了解更多：如何选择与获取 access token](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-choose-which-type-of-token-to-use)

### 路径参数

名称 | 类型 | 描述
---|---|---
space_id | string | [知识空间id](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-overview)，如果查询**我的文档库**可替换为`my_library`<br>**示例值**："6946843325487906839"

### 查询参数

名称 | 类型 | 必填 | 描述
---|---|---|---
page_size | int | 否 | 分页大小<br>**示例值**：10<br>**数据校验规则**：<br>- 最大值：`50`
page_token | string | 否 | 分页标记，第一次请求不填，表示从头开始遍历；分页查询结果还有更多项时会同时返回新的 page_token，下次遍历可采用该 page_token 获取查询结果<br>**示例值**：6946843325487456878
parent_node_token | string | 否 | 父节点token<br>**示例值**：wikcnKQ1k3p******8Vabce

## 响应

### 响应体

名称 | 类型 | 描述
---|---|---
code | int | 错误码，非 0 表示失败
msg | string | 错误描述
data | \- | \-
items | node\[\] | 数据列表
space_id | string | 知识空间id<br>[获取方式](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-overview)
node_token | string | 节点token
obj_token | string | 对应文档类型的token，可根据 obj_type 判断属于哪种文档类型。
obj_type | string | 文档类型，对于快捷方式，该字段是对应的实体的obj_type。<br>**可选值有**：<br>- doc：旧版文档<br>- sheet：表格<br>- mindnote：思维导图<br>- bitable：多维表格<br>- file：文件<br>- docx：新版文档<br>- slides：幻灯片
parent_node_token | string | 父节点 token。若当前节点为一级节点，父节点 token 为空。
node_type | string | 节点类型<br>**可选值有**：<br>- origin：实体<br>- shortcut：快捷方式
origin_node_token | string | 快捷方式对应的实体node_token，当节点为快捷方式时，该值不为空。
origin_space_id | string | 快捷方式对应的实体所在的space id
has_child | boolean | 是否有子节点
title | string | 文档标题
obj_create_time | string | 文档创建时间
obj_edit_time | string | 文档最近编辑时间
node_create_time | string | 节点创建时间
creator | string | 节点创建者
owner | string | 节点所有者
node_creator | string | 节点创建者
page_token | string | 分页标记，当 has_more 为 true 时，会同时返回新的 page_token，否则不返回 page_token
has_more | boolean | 是否还有更多项

### 响应体示例
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "items": [
            {
                "space_id": "6946843325487912356",
                "node_token": "wikcnKQ1k3p******8Vabcef",
                "obj_token": "doccnzAaOD******Wabcdef",
                "obj_type": "doc",
                "parent_node_token": "wikcnKQ1k3p******8Vabcef",
                "node_type": "origin",
                "origin_node_token": "wikcnKQ1k3p******8Vabcef",
                "origin_space_id": "6946843325487912356",
                "has_child": false,
                "title": "标题",
                "obj_create_time": "1642402428",
                "obj_edit_time": "1642402428",
                "node_create_time": "1642402428",
                "creator": "ou_xxxxx",
                "owner": "ou_xxxxx",
                "node_creator": "ou_xxxxx"
            }
        ],
        "page_token": "6946843325487906839",
        "has_more": true
    }
}
```

### 错误码

HTTP状态码 | 错误码 | 描述 | 排查建议
---|---|---|---
400 | 131001 | rpc fail | 服务报错，请稍后重试，或者拿响应体的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131002 | param err | 通常为传参有误，例如数据类型不匹配。请查看**具体接口报错信息**，报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131004 | invalid user | 非法用户（如未登陆或用户 ID 校验失败）。请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131005 | not found | 未找到相关数据，例如id不存在。相关报错信息参考：<br>- member not found：用户不是知识空间成员（管理员），无法删除。<br>- identity not found: userid不存在，无法添加/删除成员。<br>- space not found：知识空间不存在<br>- node not found：节点不存在<br>- document not found：文档不存在<br>报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131006 | permission denied | 权限拒绝，相关报错信息参考：<br>- wiki space permission denied：知识库权限鉴权不通过，需要成为知识空间管理员（成员）。<br>- node permission denied：文档节点权限鉴权不通过，读操作需要具备节点阅读权限，写操作（创建、移动等）则需要具备节点容器编辑权限。<br>- no source parent node permission：需要具备原父节点的容器编辑权限。<br>- no destination parent node permission：需要具备目标父节点的容器编辑权限，若移动到知识空间下，则需要成为知识空间管理员（成员）。<br>**注意**：应用访问或操作文档时，除了申请 API 权限，还需授权具体文档资源的阅读、编辑或管理权限。<br>请参考以下步骤操作： <br>1. **当遇到资源权限不足的情况**：参阅[如何给应用授权访问知识库文档资源](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#a40ad4ca)。<br>2. **也可直接将应用添加为知识库管理员（成员）**：参阅[如何将应用添加为知识库管理员（成员）](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#b5da330b)。<br>3. **若无法解决或报错信息不明确时**：请咨询[技术支持](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131007 | internal err | 服务内部错误，请勿重试，拿返回值的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。

# 更新知识空间节点标题

此接口用于更新节点标题

**注意事项**：此接口目前仅支持文档(doc)、新版文档(docx)和快捷方式。

## 请求

基本 | &nbsp;
---|---
HTTP URL | https://open.feishu.cn/open-apis/wiki/v2/spaces/:space_id/nodes/:node_token/update_title
HTTP Method | POST
接口频率限制 | [100 次/分钟](https://open.feishu.cn/document/ukTMukTMukTM/uUzN04SN3QjL1cDN)
支持的应用类型 | Custom App、Store App
权限要求<br>**调用该 API 所需的权限。开启其中任意一项权限即可调用**<br>开启任一权限即可 | 更新知识空间节点信息(wiki:node:update)<br>查看、编辑和管理知识库(wiki:wiki)

### 请求头

名称 | 类型 | 必填 | 描述
---|---|---|---
Authorization | string | 是 | `tenant_access_token`<br>或<br>`user_access_token`<br>**值格式**："Bearer `access_token`"<br>**示例值**："Bearer u-7f1bcd13fc57d46bac21793a18e560"<br>[了解更多：如何选择与获取 access token](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-choose-which-type-of-token-to-use)
Content-Type | string | 是 | **固定值**："application/json; charset=utf-8"

### 路径参数

名称 | 类型 | 描述
---|---|---
space_id | string | 知识空间ID<br>**示例值**："6946843325487912356"
node_token | string | 节点token<br>**示例值**："wikcnKQ1k3pcuo5uSK4t8Vabcef"

### 请求体

名称 | 类型 | 必填 | 描述
---|---|---|---
title | string | 是 | 节点新标题<br>**示例值**："新标题"

### 请求体示例
```json
{
    "title": "新标题"
}
```

## 响应

### 响应体

名称 | 类型 | 描述
---|---|---
code | int | 错误码，非 0 表示失败
msg | string | 错误描述
data | \- | \-

### 响应体示例
```json
{
    "code": 0,
    "msg": "success",
    "data": {}
}
```

### 错误码

HTTP状态码 | 错误码 | 描述 | 排查建议
---|---|---|---
400 | 131001 | rpc fail | 服务报错，请稍后重试，或者拿响应体的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131002 | param err | 通常为传参有误，例如数据类型不匹配。请查看**具体接口报错信息**，报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131004 | invalid user | 非法用户。请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131005 | not found | 未找到相关数据，例如id不存在。相关报错信息参考：<br>- member not found：用户不是知识空间成员（管理员），无法删除。<br>- identity not found: userid不存在，无法添加/删除成员。<br>- space not found：知识空间不存在<br>- node not found：节点不存在<br>- document not found：文档不存在<br>报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131006 | permission denied | 权限拒绝，相关报错信息参考：<br>- wiki space permission denied：知识库权限鉴权不通过，需要成为知识空间管理员（成员）。<br>- node permission denied：文档节点权限鉴权不通过，读操作需要具备节点阅读权限，写操作（创建、移动等）则需要具备节点容器编辑权限。<br>- no source parent node permission：需要具备原父节点的容器编辑权限。<br>- no destination parent node permission：需要具备目标父节点的容器编辑权限，若移动到知识空间下，则需要成为知识空间管理员（成员）。<br>**注意**：应用访问或操作文档时，除了申请 API 权限，还需授权具体文档资源的阅读、编辑或管理权限。<br>请参考以下步骤操作： <br>1. **当遇到资源权限不足的情况**：参阅[如何给应用授权访问知识库文档资源](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#a40ad4ca)。<br>2. **也可直接将应用添加为知识库管理员（成员）**：参阅[如何将应用添加为知识库管理员（成员）](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#b5da330b)。<br>3. **若无法解决或报错信息不明确时**：请咨询[技术支持](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131007 | internal err | 服务内部错误，请勿重试，拿返回值的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。

# 移动知识空间节点

此方法用于在Wiki内移动节点，支持跨知识空间移动。如果有子节点，会携带子节点一起移动。

**注意事项**：知识库权限要求：
- 节点编辑权限
- 原父节点容器编辑权限
- 目的父节点容器编辑权限

## 请求

基本 | &nbsp;
---|---
HTTP URL | https://open.feishu.cn/open-apis/wiki/v2/spaces/:space_id/nodes/:node_token/move
HTTP Method | POST
接口频率限制 | [100 次/分钟](https://open.feishu.cn/document/ukTMukTMukTM/uUzN04SN3QjL1cDN)
支持的应用类型 | Custom App、Store App
权限要求<br>**调用该 API 所需的权限。开启其中任意一项权限即可调用**<br>开启任一权限即可 | 移动知识空间节点(wiki:node:move)<br>查看、编辑和管理知识库(wiki:wiki)<br>查看知识库(wiki:wiki:readonly)

### 请求头

名称 | 类型 | 必填 | 描述
---|---|---|---
Authorization | string | 是 | `tenant_access_token`<br>或<br>`user_access_token`<br>**值格式**："Bearer `access_token`"<br>**示例值**："Bearer u-7f1bcd13fc57d46bac21793a18e560"<br>[了解更多：如何选择与获取 access token](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-choose-which-type-of-token-to-use)
Content-Type | string | 是 | **固定值**："application/json; charset=utf-8"

### 路径参数

名称 | 类型 | 描述
---|---|---
space_id | string | 知识空间id<br>**示例值**："7008061636015512345"
node_token | string | 需要迁移的节点token<br>**示例值**："wikbcd6ydSUyOEzbdlt1BfpA5Yc"

### 请求体

名称 | 类型 | 必填 | 描述
---|---|---|---
target_parent_token | string | 否 | 移动到的父节点token<br>**示例值**："wikbcd6ydSUyOEzbdlt1BfpA5Yc"
target_space_id | string | 否 | 移动到的知识空间ID<br>**示例值**："7008061636015512345"

### 请求体示例
```json
{
    "target_parent_token": "wikbcd6ydSUyOEzbdlt1BfpA5Yc",
    "target_space_id": "7008061636015512345"
}
```

## 响应

### 响应体

名称 | 类型 | 描述
---|---|---
code | int | 错误码，非 0 表示失败
msg | string | 错误描述
data | \- | \-
node | node | 移动后的节点信息
space_id | string | 知识空间id<br>[获取方式](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-overview)
node_token | string | 节点token
obj_token | string | 对应文档类型的token，可根据 obj_type 判断属于哪种文档类型。
obj_type | string | 文档类型，对于快捷方式，该字段是对应的实体的obj_type。<br>**可选值有**：<br>- doc：旧版文档<br>- sheet：表格<br>- mindnote：思维导图<br>- bitable：多维表格<br>- file：文件<br>- docx：新版文档<br>- slides：幻灯片
parent_node_token | string | 父节点 token。若当前节点为一级节点，父节点 token 为空。
node_type | string | 节点类型<br>**可选值有**：<br>- origin：实体<br>- shortcut：快捷方式
origin_node_token | string | 快捷方式对应的实体node_token，当节点为快捷方式时，该值不为空。
origin_space_id | string | 快捷方式对应的实体所在的space id
has_child | boolean | 是否有子节点
title | string | 文档标题
obj_create_time | string | 文档创建时间
obj_edit_time | string | 文档最近编辑时间
node_create_time | string | 节点创建时间
creator | string | 节点创建者
owner | string | 节点所有者
node_creator | string | 节点创建者

### 响应体示例
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "node": {
            "space_id": "6946843325487912356",
            "node_token": "wikcnKQ1k3p******8Vabcef",
            "obj_token": "doccnzAaOD******Wabcdef",
            "obj_type": "doc",
            "parent_node_token": "wikcnKQ1k3p******8Vabcef",
            "node_type": "origin",
            "origin_node_token": "wikcnKQ1k3p******8Vabcef",
            "origin_space_id": "6946843325487912356",
            "has_child": false,
            "title": "标题",
            "obj_create_time": "1642402428",
            "obj_edit_time": "1642402428",
            "node_create_time": "1642402428",
            "creator": "ou_xxxxx",
            "owner": "ou_xxxxx",
            "node_creator": "ou_xxxxx"
        }
    }
}
```

### 错误码

HTTP状态码 | 错误码 | 描述 | 排查建议
---|---|---|---
400 | 131001 | rpc fail | 服务报错，请稍后重试，或者拿响应体的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131002 | param err | 通常为传参有误，例如数据类型不匹配。请查看**具体接口报错信息**，报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131003 | out of limit | 超出操作限制，例如节点数量限制。请参阅下表。<br>- 原/目标知识空间总节点数不超过40万。<br>- 原/目标知识空间目录树不超过50层。<br>- 目的父节点下单层节点数不超过2000。<br>- 单次移动节点数（带子节点）不超过2000。
400 | 131004 | invalid user | 非法用户。请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131005 | not found | 未找到相关数据，例如id不存在。相关报错信息参考：<br>- member not found：用户不是知识空间成员（管理员），无法删除。<br>- identity not found: userid不存在，无法添加/删除成员。<br>- space not found：知识空间不存在<br>- node not found：节点不存在<br>- document not found：文档不存在<br>报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131006 | permission denied | 权限拒绝，相关报错信息参考：<br>- wiki space permission denied：知识库权限鉴权不通过，需要成为知识空间管理员（成员）。<br>- node permission denied：文档节点权限鉴权不通过，读操作需要具备节点阅读权限，写操作（创建、移动等）则需要具备节点容器编辑权限。<br>- no source parent node permission：需要具备原父节点的容器编辑权限。<br>- no destination parent node permission：需要具备目标父节点的容器编辑权限，若移动到知识空间下，则需要成为知识空间管理员（成员）。<br>**注意**：应用访问或操作文档时，除了申请 API 权限，还需授权具体文档资源的阅读、编辑或管理权限。<br>请参考以下步骤操作： <br>1. **当遇到资源权限不足的情况**：参阅[如何给应用授权访问知识库文档资源](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#a40ad4ca)。<br>2. **也可直接将应用添加为知识库管理员（成员）**：参阅[如何将应用添加为知识库管理员（成员）](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#b5da330b)。<br>3. **若无法解决或报错信息不明确时**：请咨询[技术支持](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131007 | internal err | 服务内部错误，请勿重试，拿返回值的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。

# 创建知识空间节点副本

此接口用于在知识空间创建节点副本到指定位置。

## 请求

基本 | &nbsp;
---|---
HTTP URL | https://open.feishu.cn/open-apis/wiki/v2/spaces/:space_id/nodes/:node_token/copy
HTTP Method | POST
接口频率限制 | [100 次/分钟](https://open.feishu.cn/document/ukTMukTMukTM/uUzN04SN3QjL1cDN)
支持的应用类型 | Custom App、Store App
权限要求<br>**调用该 API 所需的权限。开启其中任意一项权限即可调用**<br>开启任一权限即可 | 创建知识空间节点副本(wiki:node:copy)<br>查看、编辑和管理知识库(wiki:wiki)

### 请求头

名称 | 类型 | 必填 | 描述
---|---|---|---
Authorization | string | 是 | `tenant_access_token`<br>或<br>`user_access_token`<br>**值格式**："Bearer `access_token`"<br>**示例值**："Bearer u-7f1bcd13fc57d46bac21793a18e560"<br>[了解更多：如何选择与获取 access token](https://open.feishu.cn/document/uAjLw4CM/ugTN1YjL4UTN24CO1UjN/trouble-shooting/how-to-choose-which-type-of-token-to-use)
Content-Type | string | 是 | **固定值**："application/json; charset=utf-8"

### 路径参数

名称 | 类型 | 描述
---|---|---
space_id | string | 知识空间id<br>**示例值**："6946843325487912356"
node_token | string | 节点token<br>**示例值**："wikcnKQ1k3p******8Vabce"

### 请求体

名称 | 类型 | 必填 | 描述
---|---|---|---
target_parent_token | string | 否 | 目标父节点 Token。<br>- 目标知识空间 ID 与目标父节点 Token 不可同时为空。<br>**示例值**："wikcnKQ1k3p******8Vabce"<br>**数据校验规则**：<br>- 长度范围：`0` ～ `999` 字符
target_space_id | string | 否 | 目标知识空间 ID。<br>- 目标知识空间 ID 与目标父节点 Token 不可同时为空。<br>**示例值**："6946843325487912356"
title | string | 否 | 复制后的新标题。如果填空，则新标题为空。如果不填，则使用原节点标题。<br>**示例值**："新标题。"

### 请求体示例
```json
{
    "target_parent_token": "wikcnKQ1k3p******8Vabce",
    "target_space_id": "6946843325487912356",
    "title": "新标题。"
}
```

## 响应

### 响应体

名称 | 类型 | 描述
---|---|---
code | int | 错误码，非 0 表示失败
msg | string | 错误描述
data | \- | \-
node | node | 创建副本后的新节点
space_id | string | 知识空间id<br>[获取方式](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-overview)
node_token | string | 节点token
obj_token | string | 对应文档类型的token，可根据 obj_type 判断属于哪种文档类型。
obj_type | string | 文档类型，对于快捷方式，该字段是对应的实体的obj_type。<br>**可选值有**：<br>- doc：旧版文档<br>- sheet：表格<br>- mindnote：思维导图<br>- bitable：多维表格<br>- file：文件<br>- docx：新版文档<br>- slides：幻灯片
parent_node_token | string | 父节点 token。若当前节点为一级节点，父节点 token 为空。
node_type | string | 节点类型<br>**可选值有**：<br>- origin：实体<br>- shortcut：快捷方式
origin_node_token | string | 快捷方式对应的实体node_token，当节点为快捷方式时，该值不为空。
origin_space_id | string | 快捷方式对应的实体所在的space id
has_child | boolean | 是否有子节点
title | string | 文档标题
obj_create_time | string | 文档创建时间
obj_edit_time | string | 文档最近编辑时间
node_create_time | string | 节点创建时间
creator | string | 节点创建者
owner | string | 节点所有者
node_creator | string | 节点创建者

### 响应体示例
```json
{
    "code": 0,
    "msg": "success",
    "data": {
        "node": {
            "space_id": "6946843325487912356",
            "node_token": "wikcnKQ1k3p******8Vabcef",
            "obj_token": "doccnzAaOD******Wabcdef",
            "obj_type": "doc",
            "parent_node_token": "wikcnKQ1k3p******8Vabcef",
            "node_type": "origin",
            "origin_node_token": "wikcnKQ1k3p******8Vabcef",
            "origin_space_id": "6946843325487912356",
            "has_child": false,
            "title": "标题",
            "obj_create_time": "1642402428",
            "obj_edit_time": "1642402428",
            "node_create_time": "1642402428",
            "creator": "ou_xxxxx",
            "owner": "ou_xxxxx",
            "node_creator": "ou_xxxxx"
        }
    }
}
```

### 错误码

HTTP状态码 | 错误码 | 描述 | 排查建议
---|---|---|---
400 | 131001 | rpc fail | 服务报错，请稍后重试，或者拿响应体的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131002 | param err | 通常为传参有误，例如数据类型不匹配。请查看**具体接口报错信息**，报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131003 | out of limit | 超出操作限制，例如节点数量限制。请参阅下表。<br>- 原/目标知识空间总节点数不超过40万。<br>- 原/目标知识空间目录树不超过50层。<br>- 目的父节点下单层节点数不超过2000。<br>- 单次移动节点数（带子节点）不超过2000。
400 | 131004 | invalid user | 非法用户。请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131005 | not found | 未找到相关数据，例如id不存在。相关报错信息参考：<br>- member not found：用户不是知识空间成员（管理员），无法删除。<br>- identity not found: userid不存在，无法添加/删除成员。<br>- space not found：知识空间不存在<br>- node not found：节点不存在<br>- document not found：文档不存在<br>报错不明确时请咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131006 | permission denied | 权限拒绝，相关报错信息参考：<br>- wiki space permission denied：知识库权限鉴权不通过，需要成为知识空间管理员（成员）。<br>- node permission denied：文档节点权限鉴权不通过，读操作需要具备节点阅读权限，写操作（创建、移动等）则需要具备节点容器编辑权限。<br>- no source parent node permission：需要具备原父节点的容器编辑权限。<br>- no destination parent node permission：需要具备目标父节点的容器编辑权限，若移动到知识空间下，则需要成为知识空间管理员（成员）。<br>**注意**：应用访问或操作文档时，除了申请 API 权限，还需授权具体文档资源的阅读、编辑或管理权限。<br>请参考以下步骤操作： <br>1. **当遇到资源权限不足的情况**：参阅[如何给应用授权访问知识库文档资源](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#a40ad4ca)。<br>2. **也可直接将应用添加为知识库管理员（成员）**：参阅[如何将应用添加为知识库管理员（成员）](https://open.feishu.cn/document/ukTMukTMukTM/uUDN04SN0QjL1QDN/wiki-v2/wiki-qa#b5da330b)。<br>3. **若无法解决或报错信息不明确时**：请咨询[技术支持](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)。
400 | 131007 | internal err | 服务内部错误，请勿重试，拿返回值的header头里的x-tt-logid咨询[oncall](https://applink.feishu.cn/client/helpdesk/open?id=6626260912531570952)定位。
400 | 131009 | lock contention, please retry later. | 并发请求异常，请稍后重试。
