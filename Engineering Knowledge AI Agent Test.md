 
 ## Question

1. Describe differences between REST API, MCP in the context of AI.
2. How REST API, MCP, can improve the AI use case.
3. How do you ensure that your AI agent answers correctly?
4. Describe what can you do with Docker / Containerize environment in the context of AI
5. How do you finetune the LLM model from raw ?

## Answer
1. REST API is a standard way for two computer programs to communicate over the internet, usually using HTTP. In AI it can be used to send the input like text or image to the model and then get the prediction back, or also can be used as a set of tools that AI Agent can call, for example a web search API where the agent just need to send the query parameter and then it will get the search result back to be used in generating the answer. While REST API is a general purpose and already widely used outside of AI, the MCP which stands for Model Context Protocol, is designed more specific for AI and LLM applications to manage and interact with external tools, system or even the REST API itself. The difference is, if we want to use REST API with the AI Agent we need to manually define the list of APIs, what parameters they accept and what kind of response will come back, but with MCP it give another abstraction layer where the AI Agent can just ask the MCP server in runtime to know what tools are available and how to use them. This make MCP more suitable for complex and dynamic flow.

2. Both of them allow the AI Agent to connect with other system without the need to reinvent or create the functionality from scratch. For example we don’t need to build our own search engine, we just use the Google Search API and only need to know what parameters should be sent and what kind of response will be returned. This save time and also make the agent more powerful by combining many existing services.

3. To make sure the AI Agent answer correctly, first we should use RAG with proper prompt engineering, including giving guidelines and prohibitions, instead of directly using the LLM answer itself. Second, we can prepare evaluation metrics like faithfulness and correctness before deployment, so we can test if the RAG application already able to answer the sample questions properly and based on the right context. And then when deployed, we can also add some guardrails for special cases like blocking competitor names or dangerous content, and also monitoring by collecting user feedback through thumbs up and down or other signals such as how many users ask to connect with human agent.

4. With Docker or containerized environment it become easy to reproduce the same environment everywhere and avoid the problem of “it works on my machine”. It is also easy to scale when deploying with Kubernetes because we can configure how many pods should run the container, and if need more capacity we just increase the number of pods. Container also can be integrated with CI/CD pipeline so the deployment process can be automated and even done with zero downtime.

5. If we use a pre-trained model like LLaMA, Gemma or Qwen, first we need to define the task that we want the model to do. After that we collect or build the dataset for that task, for example for dialogue summarization we can use the DialogSum dataset. By defining the task we also can define the evaluation metric, in this example we can use ROUGE score. Then we can use library like Unsloth to fine tune the model using LoRA method, because fine tuning the full model will need very large GPU and cost. With LoRA we only fine tune small adapter matrices that are attached to the LLM instead of updating the whole weight, so it is faster and cheaper but still effective.
