from langchain_core.messages import HumanMessage

const = [1,2,3,4]
content = [
        {"test": "test"},
    ]

imgs = {}

if 1==0:
    for i in range(4):
        print(i-1)
        content.append({f"test{i}": f"test_{i}"})


msg = HumanMessage(
    content = content
)
#print(msg)

test = 5
test =- 1
print(test)

folder_name = "asd"

full_path = f"./user_input/raw/{folder_name}"
