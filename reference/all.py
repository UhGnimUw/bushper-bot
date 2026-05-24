from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import yaml


with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

llm = ChatOpenAI(model=config["local_model_name"], temperature=config["local_model_temperature"], base_url=config["local_model_url"], api_key="not-needed")


prompt_template = ChatPromptTemplate.from_messages([
    ("system", "你是一位专业的{role}。"),
    ("user", "{content}")
])

output_parser = StrOutputParser()
chain = prompt_template | llm | output_parser


input = "你好,介绍一下量子力学"
result = chain.invoke({"role": "专业的助手", "content": input})
print(result)