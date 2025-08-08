from sqlalchemy import create_engine,text
from utils import hash_password , create_access_token, verify_password
import pandas as pd
from pydantic import BaseModel

class TokenResponse(BaseModel):
    responseStatus:int
    message:str
    access_token: str
    token_type: str = ""

def userRegistration(param):
    print(param)
    DATABASE_URL='postgresql://neondb_owner:npg_0NhJsCfg2HUT@ep-lingering-truth-ad83kw5t.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require'
    engine = create_engine(DATABASE_URL)
    params = {}
    base_query = """
        select * from gateway.lending_auth where no_hp = :no_hp
    """
    params['no_hp'] = param.no_hp

    data = pd.read_sql(text(base_query), engine, params=params)
    print(len(data))
    if len(data) ==0:
    # Insert ke table lain (atau sama)
        insert_query = text("""
            INSERT INTO gateway.lending_auth (username, email, no_hp, password)
            VALUES (:username, :email, :no_hp, :password)
        """)
        insert_params = {
            "username": param.username,
            "email": param.email,
            "no_hp": param.no_hp,
            "password": hash_password(param.password)  # hash dulu sebelumnya ya
        }

        with engine.connect() as conn:
            conn.execute(insert_query, insert_params)
            conn.commit()
            
        return {
            "responseStatus": 201,
            "message":'Create account successfully',
            "result": params
        }
    else:
        return {
            "responseStatus": 409,
            "message":'Account with the phone number already exist',
        }
    
async def userLogin(payload,db):
    user = await db.fetchrow("SELECT * FROM gateway.lending_auth WHERE no_hp = $1", payload.no_hp)

    if not user:
        return TokenResponse(responseStatus=404,message='Account not found',access_token="")

    if not verify_password(payload.password, user["password"]):
        return TokenResponse(responseStatus=401,message='Phone number or Password invalid',access_token="")
        # raise HTTPException(status_code=401, detail="Password salah")

    token = create_access_token(data={"username": user["username"], "email":user['email']})

    return TokenResponse(responseStatus=201,message='Login successfully',access_token=token, token_type='bearer')
