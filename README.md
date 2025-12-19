conda activate Yolo-vHeat

http://localhost:8000/api/docs
POST /api/v1/auth/register，点击 Try it out，填入：
{
  "username": "teacher001",
  "email": "teacher@example.com",
  "password": "123456",
  "role": "teacher",
  "unit": "实验中学",
  "class_name": "高一(1)班"
}

cd "H:\毕业设计\System\System\frontend"
streamlit run app.py

cd "H:\毕业设计\System\backend"
python run.py