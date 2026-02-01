> ## Documentation Index
> Fetch the complete documentation index at: https://docs.bigmodel.cn/llms.txt
> Use this file to discover all available pages before exploring further.

# HTTP API 调用

智谱AI 提供基于 RESTful 架构的应用程序接口，通过标准的 HTTP 协议与智谱AI 的模型服务进行交互。无论您使用什么编程语言或开发框架，都可以通过 HTTP 请求来调用智谱AI 的各种 AI 模型。

### 核心优势

<CardGroup cols={2}>
  <Card title="跨平台兼容" icon={<svg style={{maskImage: "url(/resource/icon/globe.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"}/>}>
    支持所有支持 HTTP 协议的编程语言和平台
  </Card>

  <Card title="标准协议" icon={<svg style={{maskImage: "url(/resource/icon/shield-check.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"}/>}>
    基于 RESTful 设计，遵循 HTTP 标准，易于理解和使用
  </Card>

  <Card title="灵活集成" icon={<svg style={{maskImage: "url(/resource/icon/puzzle-piece.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"}/>}>
    可以集成到任何现有的应用程序和系统中
  </Card>

  <Card title="实时调用" icon={<svg style={{maskImage: "url(/resource/icon/bolt.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"}/>}>
    支持同步和异步调用，满足不同场景需求
  </Card>
</CardGroup>

## 获取 API Key

1. 访问 [智谱AI 开放平台](https://bigmodel.cn)
2. 注册并登录您的账户
3. 在 [API Keys](https://bigmodel.cn/usercenter/proj-mgmt/apikeys) 管理页面创建 API Key
4. 复制您的 API Key 以供使用

<Tip>
  建议将 API Key 设置为环境变量替代硬编码到代码中，以提高安全性。
</Tip>

## API 基础信息

### 请求端点(通用API)

```
https://open.bigmodel.cn/api/paas/v4/
```

<Warning>
  注意：使用 [GLM 编码套餐](/cn/coding-plan/overview) 时，需要配置专属的 \
  Coding 端点 - [https://open.bigmodel.cn/api/coding/paas/v4](https://open.bigmodel.cn/api/coding/paas/v4) \
  而非通用端点 - [https://open.bigmodel.cn/api/paas/v4/](https://open.bigmodel.cn/api/paas/v4/) \
  注意：Coding API 端点仅限 Coding 场景，并不适用通用 API 场景，请区分使用。
</Warning>

### 请求头要求

<mcreference link="https://bigmodel.cn/dev/api/http-call/http-para" index="0">0</mcreference>

```http  theme={null}
Content-Type: application/json
Authorization: Bearer YOUR_API_KEY
```

### 支持的鉴权方式

<Tabs>
  <Tab title="API Key 鉴权">
    最简单的鉴权方式，直接使用您的 API Key：

    ```bash  theme={null}
    curl --location 'https://open.bigmodel.cn/api/paas/v4/chat/completions' \
    --header 'Authorization: Bearer YOUR_API_KEY' \
    --header 'Content-Type: application/json' \
    --data '{
        "model": "glm-4.7",
        "messages": [
            {
                "role": "user",
                "content": "你好"
            }
        ]
    }'
    ```
  </Tab>

  <Tab title="JWT Token 鉴权">
    使用 JWT Token 进行鉴权，适合需要更高安全性的场景：
    安装依赖 PyJWT

    ```shell  theme={null}
    pip install PyJWT
    ```

    ```python  theme={null}
    import time
    import jwt

    def generate_token(apikey: str, exp_seconds: int):
        try:
            id, secret = apikey.split(".")
        except Exception as e:
            raise Exception("invalid apikey", e)

        payload = {
            "api_key": id,
            "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
            "timestamp": int(round(time.time() * 1000)),
        }

        return jwt.encode(
            payload,
            secret,
            algorithm="HS256",
            headers={"alg": "HS256", "sign_type": "SIGN"},
        )

    # 使用生成的 token
    token = generate_token("your-api-key", 3600)  # 1 小时有效期
    ```
  </Tab>
</Tabs>

## 基础调用示例

### 简单对话

```bash  theme={null}
curl --location 'https://open.bigmodel.cn/api/paas/v4/chat/completions' \
--header 'Authorization: Bearer YOUR_API_KEY' \
--header 'Content-Type: application/json' \
--data '{
    "model": "glm-4.7",
    "messages": [
        {
            "role": "user",
            "content": "请介绍一下人工智能的发展历程"
        }
    ],
    "temperature": 1.0,
    "max_tokens": 1024
}'
```

### 流式响应

```bash  theme={null}
curl --location 'https://open.bigmodel.cn/api/paas/v4/chat/completions' \
--header 'Authorization: Bearer YOUR_API_KEY' \
--header 'Content-Type: application/json' \
--data '{
    "model": "glm-4.7",
    "messages": [
        {
            "role": "user",
            "content": "写一首关于春天的诗"
        }
    ],
    "stream": true
}'
```

### 多轮对话

```bash  theme={null}
curl --location 'https://open.bigmodel.cn/api/paas/v4/chat/completions' \
--header 'Authorization: Bearer YOUR_API_KEY' \
--header 'Content-Type: application/json' \
--data '{
    "model": "glm-4.7",
    "messages": [
        {
            "role": "system",
            "content": "你是一个专业的编程助手"
        },
        {
            "role": "user",
            "content": "什么是递归？"
        },
        {
            "role": "assistant",
            "content": "递归是一种编程技术，函数调用自身来解决问题..."
        },
        {
            "role": "user",
            "content": "能给我一个 Python 递归的例子吗？"
        }
    ]
}'
```

## 常用编程语言示例

<Tabs>
  <Tab title="Python">
    ```python  theme={null}
    import requests
    import json

    def call_zhipu_api(messages, model="glm-4.7"):
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"

        headers = {
            "Authorization": "Bearer YOUR_API_KEY",
            "Content-Type": "application/json"
        }

        data = {
            "model": model,
            "messages": messages,
            "temperature": 1.0
        }

        response = requests.post(url, headers=headers, json=data)

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"API调用失败: {response.status_code}, {response.text}")

    # 使用示例
    messages = [
        {"role": "user", "content": "你好，请介绍一下自己"}
    ]

    result = call_zhipu_api(messages)
    print(result['choices'][0]['message']['content'])
    ```
  </Tab>

  <Tab title="JavaScript">
    ```javascript  theme={null}
    async function callZhipuAPI(messages, model = 'glm-4.7') {
        const url = 'https://open.bigmodel.cn/api/paas/v4/chat/completions';

        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Authorization': 'Bearer YOUR_API_KEY',
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                messages: messages,
                temperature: 1.0
            })
        });

        if (!response.ok) {
            throw new Error(`API 调用失败: ${response.status}`);
        }

        return await response.json();
    }

    // 使用示例
    const messages = [
        { role: 'user', content: '你好，请介绍一下自己' }
    ];

    callZhipuAPI(messages)
        .then(result => {
            console.log(result.choices[0].message.content);
        })
        .catch(error => {
            console.error('错误:', error);
        });
    ```
  </Tab>

  <Tab title="Java">
    ```java  theme={null}
    import com.fasterxml.jackson.databind.ObjectMapper;
    import okhttp3.MediaType;
    import okhttp3.OkHttpClient;
    import okhttp3.Request;
    import okhttp3.RequestBody;
    import okhttp3.Response;
    import java.util.Collections;
    import java.util.HashMap;
    import java.util.Map;

    public class AgentExample {

        public static void main(String[] args) throws Exception {

            OkHttpClient client = new OkHttpClient();
            ObjectMapper mapper = new ObjectMapper();
            Map<String, String> messages = new HashMap<>(8);
            messages.put("role", "user");
            messages.put("content", "你好，请介绍一下自己");
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("model", "glm-4.7");
            requestBody.put("messages", Collections.singletonList(messages));
            requestBody.put("temperature", 1.0);

            String jsonBody = mapper.writeValueAsString(requestBody);
            MediaType JSON = MediaType.get("application/json; charset=utf-8");
            RequestBody body = RequestBody.create(JSON, jsonBody);
            Request request = new Request.Builder()
                .url("https://open.bigmodel.cn/api/paas/v4/chat/completions")
                .addHeader("Authorization", "Bearer your_api_key")
                .addHeader("Content-Type", "application/json")
                .post(body)
                .build();
            try (Response response = client.newCall(request).execute()) {
                System.out.println(response.body().string());
            }
        }
    }
    ```
  </Tab>
</Tabs>

## 错误处理

### 常见错误码

| 错误码 | 说明      | 解决方案            |
| --- | ------- | --------------- |
| 401 | 未授权     | 检查 API Key 是否正确 |
| 429 | 请求过于频繁  | 降低请求频率，实施重试机制   |
| 500 | 服务器内部错误 | 稍后重试，如持续出现请联系支持 |

更多错误码和解决方案请参考 [API 错误码文档](/cn/faq/api-code)

## 实践建议

<CardGroup cols={2}>
  <Card title="安全性">
    * 妥善保管 API Key，不要在代码中硬编码
    * 使用环境变量或配置文件存储敏感信息
    * 定期轮换 API Key
  </Card>

  <Card title="性能优化">
    * 实施连接池和会话复用
    * 合理设置超时时间
    * 使用异步请求处理高并发场景
  </Card>

  <Card title="错误处理">
    * 实施指数退避重试机制
    * 记录详细的错误日志
    * 设置合理的超时和重试次数
  </Card>

  <Card title="监控">
    * 监控 API 调用频率和成功率
    * 跟踪响应时间和错误率
    * 设置告警机制
  </Card>
</CardGroup>

## 更多资源

<CardGroup cols={2}>
  <Card title="API 文档" icon={<svg style={{maskImage: "url(/resource/icon/book.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"}/>} href="/cn/api/introduction">
    查看完整的 API 接口文档和参数说明
  </Card>

  <Card title="技术支持" icon={<svg style={{maskImage: "url(/resource/icon/headset.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"}/>} href="https://bigmodel.cn/online-book/customerService">
    获取技术支持和帮助
  </Card>
</CardGroup>

<Note>
  建议在生产环境中使用 HTTPS 协议，并实施适当的安全措施来保护您的 API 密钥和数据传输。
</Note>

> ## Documentation Index
> Fetch the complete documentation index at: https://docs.bigmodel.cn/llms.txt
> Use this file to discover all available pages before exploring further.

# GLM-4.7-Flash

## <div className="flex items-center"> <svg style={{maskImage: "url(/resource/icon/rectangle-list.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} /> 概览 </div>

GLM-4.7-Flash 作为 30B 级 SOTA 模型，提供了一个兼顾性能与效率的新选择。面向 **Agentic Coding** 场景强化了编码能力、长程任务规划与工具协同，并在多个公开基准的当期榜单中取得同尺寸开源模型中的出色表现。在执行复杂智能体任务，在工具调用时指令遵循更强，Artifacts 与 Agentic Coding 的前端美感和长程任务完成效率进一步提升。

<CardGroup cols={2}>
  <Card title="输入模态" icon={<svg style={{maskImage: "url(/resource/icon/arrow-down-right.svg)", WebkitMaskImage: "url(/resource/icon/arrow-down-right.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />}>
    文本
  </Card>

  <Card title="输出模态" icon={<svg style={{maskImage: "url(/resource/icon/arrow-down-left.svg)", WebkitMaskImage: "url(/resource/icon/arrow-down-left.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />}>
    文本
  </Card>

  <Card title="上下文窗口" icon={<svg style={{maskImage: "url(/resource/icon/arrow-down-arrow-up.svg)", WebkitMaskImage: "url(/resource/icon/arrow-down-arrow-up.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />}>
    200K
  </Card>

  <Card title="最大输出 Tokens" icon={<svg style={{maskImage: "url(/resource/icon/maximize.svg)", WebkitMaskImage: "url(/resource/icon/maximize.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />}>
    128K
  </Card>
</CardGroup>

## <div className="flex items-center"> <svg style={{maskImage: "url(/resource/icon/bolt.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} /> 能力支持 </div>

<CardGroup cols={3}>
  <Card title="思考模式" icon={<svg style={{maskImage: "url(/resource/icon/brain.svg)", WebkitMaskImage: "url(/resource/icon/brain.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />} href="/cn/guide/capabilities/thinking-mode">
    提供多种思考模式，覆盖不同任务需求
  </Card>

  <Card title="流式输出" icon={<svg style={{maskImage: "url(/resource/icon/maximize.svg)", WebkitMaskImage: "url(/resource/icon/maximize.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />} href="/cn/guide/capabilities/streaming">
    支持实时流式响应，提升用户交互体验
  </Card>

  <Card title="Function Call" icon={<svg style={{maskImage: "url(/resource/icon/function.svg)", WebkitMaskImage: "url(/resource/icon/function.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />} href="/cn/guide/capabilities/function-calling">
    强大的工具调用能力，支持多种外部工具集成
  </Card>

  <Card title="上下文缓存" icon={<svg style={{maskImage: "url(/resource/icon/database.svg)", WebkitMaskImage: "url(/resource/icon/database.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />} href="/cn/guide/capabilities/cache">
    智能缓存机制，优化长对话性能
  </Card>

  <Card title="结构化输出" icon={<svg style={{maskImage: "url(/resource/icon/code.svg)", WebkitMaskImage: "url(/resource/icon/code.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />} href="/cn/guide/capabilities/struct-output">
    支持 JSON 等结构化格式输出，便于系统集成
  </Card>

  <Card title="MCP" icon={<svg style={{maskImage: "url(/resource/icon/box.svg)", WebkitMaskImage: "url(/resource/icon/box.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />}>
    可灵活调用外部 MCP 工具与数据源，扩展应用场景
  </Card>
</CardGroup>

## <div className="flex items-center"> <svg style={{maskImage: "url(/resource/icon/stars.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} /> 推荐场景 </div>

<AccordionGroup>
  <Accordion title="Agentic Coding">
    GLM-4.7 面向「任务完成」而非单点代码生成，能够从目标描述出发，自主完成需求理解、方案拆解与多技术栈整合。在包含前后端联动、实时交互与外设调用的复杂场景中，可直接生成结构完整、可运行的代码框架，显著减少人工拼装与反复调试成本，适合复杂 Demo、原型验证与自动化开发流程。
  </Accordion>

  <Accordion title="多模态交互与实时应用开发">
    在需要摄像头、实时输入与交互控制的场景中，GLM-4.7 展现出更强的系统级理解能力。能够将视觉识别、逻辑控制与应用代码整合为统一方案，支持如手势控制、实时反馈等交互式应用的快速构建，加速从想法到可运行应用的落地过程。
  </Accordion>

  <Accordion title="前端视觉审美优化">
    对视觉代码与 UI 规范的理解显著增强。GLM-4.7 能在布局结构、配色和谐度与组件样式上给出更具美感且一致的默认方案，减少样式反复“微调”的时间成本，适合低代码平台、AI 前端生成工具及快速原型设计场景。
  </Accordion>

  <Accordion title="高质量对话与复杂问题协作">
    在多轮对话中更稳定地保持上下文与约束条件，对简单问题回应更直接，对复杂问题能够持续澄清目标并推进解决路径。GLM-4.7 更像一名可协作的“问题解决型伙伴”，适用于开发支持、方案讨论与决策辅助等高频协作场景。
  </Accordion>

  <Accordion title="沉浸式写作与角色驱动创作">
    文字表达更细腻、更具画面感，能够通过气味、声音、光影等感官细节构建氛围。在角色扮演与叙事创作中，对世界观与人设的遵循更加稳定，剧情推进自然有张力，适合互动叙事、IP 内容创作与角色型应用。
  </Accordion>

  <Accordion title="专业级 PPT / 海报生成">
    在办公创作中，GLM-4.7 的版式遵循与审美稳定性明显提升。能够稳定适配 16:9 等主流比例，在字体层级、留白与配色上减少模板感，生成结果更接近“即用级”，适合 AI 演示工具、企业办公系统与自动化内容生成场景。
  </Accordion>

  <Accordion title="智能搜索与 Deep Research">
    强化用户意图理解、信息检索与结果融合能力。在复杂问题与研究型任务中，GLM-4.7 不仅返回信息，还能进行结构化整理与跨来源整合，通过多轮交互持续逼近核心结论，适合深度研究与决策支持场景。
  </Accordion>
</AccordionGroup>

## <div className="flex items-center"> <svg style={{maskImage: "url(/resource/icon/stars.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} /> 详细介绍 </div>

<Steps>
  <Step title="小而强的 Coding Agent" icon={<svg style={{maskImage: "url(/resource/icon/star.svg)", WebkitMaskImage: "url(/resource/icon/star.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} />}>
    GLM-4.7 系列在编程、推理与智能体三个维度实现了显著突破：

    * **更强的编程能力**：显著提升了模型在多语言编码和在终端智能体中的效果；现在可以在 Claude Code、Kilo Code、TRAE、Cline 和 Roo Code 等编程框架中实现“先思考、再行动”的机制，在复杂任务上有更稳定的表现
    * **前端审美提升**：GLM-4.7 系列模型在前端生成质量方面明显进步，能够生成观感更佳的网页、PPT 、海报
    * **工具调用与协同执行更强**： 增强对复杂链路的任务拆解与流程编排能力，可在多步执行中持续校验与纠偏，更适合端到端交付类的智能体任务。
    * **通用能力增强**：GLM-4.7 系列模型的对话更简洁智能且富有人情味，写作与角色扮演更具文采与沉浸感

    在SWE-bench Verified、τ²-Bench等主流基准测试中，GLM-4.7-Flash 的综合表现在相同尺寸模型系列中取得开源SOTA分数。另外，相比于同尺寸模型，GLM-4.7-Flash同样具有出色的前端和后端开发能力。

    在内部的编程实测中，GLM-4.7-Flash在前后端任务上表现出色。在编程场景之外，我们也推荐大家在中文写作、翻译、长文本、情感/角色扮演等通用场景中体验GLM-4.7-Flash。

    ![Description](https://cdn.bigmodel.cn/markdown/176886970126120260120-084119.jpeg?attname=20260120-084119.jpeg)
  </Step>
</Steps>

## <div className="flex items-center"> <svg style={{maskImage: "url(/resource/icon/gauge-high.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} /> 使用资源 </div>

[体验中心](https://bigmodel.cn/trialcenter/modeltrial/text?modelCode=glm-4.7-flash)：快速测试模型在业务场景上的效果<br />
[接口文档](/api-reference/%E6%A8%A1%E5%9E%8B-api/%E5%AF%B9%E8%AF%9D%E8%A1%A5%E5%85%A8)：API 调用方式

## <div className="flex items-center"> <svg style={{maskImage: "url(/resource/icon/rectangle-code.svg)", maskRepeat: "no-repeat", maskPosition: "center center",}} className={"h-6 w-6 bg-primary dark:bg-primary-light !m-0 shrink-0"} /> 调用示例 </div>

以下是完整的调用示例，帮助您快速上手 GLM-4.7-Flash 模型。

<Tabs>
  <Tab title="cURL">
    **基础调用**

    ```bash  theme={null}
    curl -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer your-api-key" \
        -d '{
            "model": "glm-4.7-flash",
            "messages": [
                {
                    "role": "user",
                    "content": "作为一名营销专家，请为我的产品创作一个吸引人的口号"
                },
                {
                    "role": "assistant",
                    "content": "当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息"
                },
                {
                    "role": "user",
                    "content": "智谱AI 开放平台"
                }
            ],
            "thinking": {
                "type": "enabled"
            },
            "max_tokens": 65536,
            "temperature": 1.0
        }'
    ```

    **流式调用**

    ```bash  theme={null}
    curl -X POST "https://open.bigmodel.cn/api/paas/v4/chat/completions" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer your-api-key" \
        -d '{
            "model": "glm-4.7-flash",
            "messages": [
                {
                    "role": "user",
                    "content": "作为一名营销专家，请为我的产品创作一个吸引人的口号"
                },
                {
                    "role": "assistant",
                    "content": "当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息"
                },
                {
                    "role": "user",
                    "content": "智谱AI开放平台"
                }
            ],
            "thinking": {
                "type": "enabled"
            },
            "stream": true,
            "max_tokens": 65536,
            "temperature": 1.0
        }'
    ```
  </Tab>

  <Tab title="Python">
    **安装 SDK**

    ```bash  theme={null}
    # 安装最新版本
    pip install zai-sdk
    # 或指定版本
    pip install zai-sdk==0.2.0
    ```

    **验证安装**

    ```python  theme={null}
    import zai
    print(zai.__version__)
    ```

    **基础调用**

    ```python  theme={null}
    from zai import ZhipuAiClient

    client = ZhipuAiClient(api_key="your-api-key")  # 请填写您自己的 API Key

    response = client.chat.completions.create(
        model="glm-4.7-flash",
        messages=[
            {"role": "user", "content": "作为一名营销专家，请为我的产品创作一个吸引人的口号"},
            {"role": "assistant", "content": "当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息"},
            {"role": "user", "content": "智谱AI开放平台"}
        ],
        thinking={
            "type": "enabled",    # 启用深度思考模式
        },
        max_tokens=65536,          # 最大输出 tokens
        temperature=1.0           # 控制输出的随机性
    )

    # 获取完整回复
    print(response.choices[0].message)
    ```

    **流式调用**

    ```python  theme={null}
    from zai import ZhipuAiClient

    client = ZhipuAiClient(api_key="your-api-key")  # 请填写您自己的 API Key

    response = client.chat.completions.create(
        model="glm-4.7-flash",
        messages=[
            {"role": "user", "content": "作为一名营销专家，请为我的产品创作一个吸引人的口号"},
            {"role": "assistant", "content": "当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息"},
            {"role": "user", "content": "智谱AI开放平台"}
            ],
        thinking={
            "type": "enabled",    # 启用深度思考模式
        },
        stream=True,              # 启用流式输出
        max_tokens=65536,          # 最大输出tokens
        temperature=1.0           # 控制输出的随机性
    )

    # 流式获取回复
    for chunk in response:
        if chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end='', flush=True)

        if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='', flush=True)
    ```
  </Tab>

  <Tab title="Java">
    **安装 SDK**

    **Maven**

    ```xml  theme={null}
    <dependency>
        <groupId>ai.z.openapi</groupId>
        <artifactId>zai-sdk</artifactId>
        <version>0.3.0</version>
    </dependency>
    ```

    **Gradle (Groovy)**

    ```groovy  theme={null}
    implementation 'ai.z.openapi:zai-sdk:0.3.0'
    ```

    **基础调用**

    ```java  theme={null}
    import ai.z.openapi.ZhipuAiClient;
    import ai.z.openapi.service.model.ChatCompletionCreateParams;
    import ai.z.openapi.service.model.ChatCompletionResponse;
    import ai.z.openapi.service.model.ChatMessage;
    import ai.z.openapi.service.model.ChatMessageRole;
    import ai.z.openapi.service.model.ChatThinking;
    import java.util.Arrays;

    public class BasicChat {
        public static void main(String[] args) {
            // 初始化客户端
            ZhipuAiClient client = ZhipuAiClient.builder().ofZHIPU()
                .apiKey("your-api-key")
                .build();

            // 创建聊天完成请求
            ChatCompletionCreateParams request = ChatCompletionCreateParams.builder()
                .model("glm-4.7-flash")
                .messages(Arrays.asList(
                    ChatMessage.builder()
                        .role(ChatMessageRole.USER.value())
                        .content("作为一名营销专家，请为我的产品创作一个吸引人的口号")
                        .build(),
                    ChatMessage.builder()
                        .role(ChatMessageRole.ASSISTANT.value())
                        .content("当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息")
                        .build(),
                    ChatMessage.builder()
                        .role(ChatMessageRole.USER.value())
                        .content("智谱AI开放平台")
                        .build()
                ))
                .thinking(ChatThinking.builder().type("enabled").build())
                .maxTokens(65536)
                .temperature(1.0f)
                .build();

            // 发送请求
            ChatCompletionResponse response = client.chat().createChatCompletion(request);

            // 获取回复
            if (response.isSuccess()) {
                Object reply = response.getData().getChoices().get(0).getMessage();
                System.out.println("AI 回复: " + reply);
            } else {
                System.err.println("错误: " + response.getMsg());
            }
        }
    }
    ```

    **流式调用**

    ```java  theme={null}
    import ai.z.openapi.ZhipuAiClient;
    import ai.z.openapi.service.model.ChatCompletionCreateParams;
    import ai.z.openapi.service.model.ChatCompletionResponse;
    import ai.z.openapi.service.model.ChatMessage;
    import ai.z.openapi.service.model.ChatMessageRole;
    import ai.z.openapi.service.model.ChatThinking;
    import ai.z.openapi.service.model.Delta;
    import java.util.Arrays;

    public class StreamingChat {
        public static void main(String[] args) {
            // 初始化客户端
            ZhipuAiClient client = ZhipuAiClient.builder().ofZHIPU()
                .apiKey("your-api-key")
                .build();

            // 创建流式聊天完成请求
            ChatCompletionCreateParams request = ChatCompletionCreateParams.builder()
                .model("glm-4.7-flash")
                .messages(Arrays.asList(
                    ChatMessage.builder()
                        .role(ChatMessageRole.USER.value())
                        .content("作为一名营销专家，请为我的产品创作一个吸引人的口号")
                        .build(),
                    ChatMessage.builder()
                        .role(ChatMessageRole.ASSISTANT.value())
                        .content("当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息")
                        .build(),
                    ChatMessage.builder()
                        .role(ChatMessageRole.USER.value())
                        .content("智谱AI开放平台")
                        .build()
                ))
                .thinking(ChatThinking.builder().type("enabled").build())
                .stream(true)  // 启用流式输出
                .maxTokens(65536)
                .temperature(1.0f)
                .build();

            ChatCompletionResponse response = client.chat().createChatCompletion(request);

            if (response.isSuccess()) {
                response.getFlowable().subscribe(
                    // Process streaming message data
                    data -> {
                        if (data.getChoices() != null && !data.getChoices().isEmpty()) {
                            Delta delta = data.getChoices().get(0).getDelta();
                            System.out.print(delta + "\n");
                        }
                    },
                    // Process streaming response error
                    error -> System.err.println("\nStream error: " + error.getMessage()),
                    // Process streaming response completion event
                    () -> System.out.println("\nStreaming response completed")
                );
            } else {
                System.err.println("Error: " + response.getMsg());
            }
        }
    }
    ```
  </Tab>

  <Tab title="Python(旧)">
    **更新 SDK 至 2.1.5.20250726**

    ```bash  theme={null}
    # 安装最新版本
    pip install zhipuai

    # 或指定版本
    pip install zhipuai==2.1.5.20250726
    ```

    **基础调用**

    ```python  theme={null}
    from zhipuai import ZhipuAI

    client = ZhipuAI(api_key="your-api-key")  # 请填写您自己的 API Key

    response = client.chat.completions.create(
        model="glm-4.7-flash",
        messages=[
            {"role": "user", "content": "作为一名营销专家，请为我的产品创作一个吸引人的口号"},
            {"role": "assistant", "content": "当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息"},
            {"role": "user", "content": "智谱AI开放平台"}
        ],
        thinking={
            "type": "enabled",
        },
        max_tokens=65536,
        temperature=1.0
    )

    # 获取完整回复
    print(response.choices[0].message)
    ```

    **流式调用**

    ```python  theme={null}
    from zhipuai import ZhipuAI

    client = ZhipuAI(api_key="your-api-key")  # 请填写您自己的 API Key

    response = client.chat.completions.create(
        model="glm-4.7-flash",
        messages=[
            {"role": "user", "content": "作为一名营销专家，请为我的产品创作一个吸引人的口号"},
            {"role": "assistant", "content": "当然，要创作一个吸引人的口号，请告诉我一些关于您产品的信息"},
            {"role": "user", "content": "智谱AI开放平台"}
        ],
        thinking={
            "type": "enabled",
        },
        stream=True,              # 启用流式输出
        max_tokens=65536,
        temperature=1.0
        )

    # 流式获取回复
    for chunk in response:
        if chunk.choices[0].delta.reasoning_content:
        print(chunk.choices[0].delta.reasoning_content, end='', flush=True)

        if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='', flush=True)
    ```
  </Tab>
</Tabs>
