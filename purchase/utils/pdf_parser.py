# /purchase/utils/pdf_parser.py

import pdfplumber
from datetime import datetime
import re
import io 

def parse_purchase_pdf(uploaded_file):
    # print("--- 1. parse_purchase_pdf 함수 진입 ---") 
    result = {
        "purchased_at": None,
        "supplier": "",
        "representative": "",
        "contact": "",
        "address": "",
        "business_number": "",
        "items": [],
    }

    # 파일 스트림 변환 (유지)
    try:
        file_bytes = uploaded_file.read()
        file_stream = io.BytesIO(file_bytes)
        # print("--- 2. 파일 스트림 변환 완료 ---")
    except Exception as e:
        # print(f"--- 파일 스트림 변환 실패: {e} ---")
        raise 

    try:
        with pdfplumber.open(file_stream) as pdf:
            # print("--- 3. pdfplumber 파일 열기 성공 ---")
            
            REMOVE_WORDS = [
                "수수신신자자확확인인 전전", " 수수신신자자확확인인", "(필렛)", "필렛", "136", "회"
            ]
            
            # 1. 전체 텍스트 추출
            text = ""
            for page in pdf.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
                # print(text)
            # print("--- 4. 전체 텍스트 추출 완료 ---") 

            # 2. 전체 텍스트에서 불필요한 문자열 제거
            for word in REMOVE_WORDS:
                text = text.replace(word, "")

            # print("--- 5. 불필요한 문자열 제거 완료 ---")
            # print(repr(text))

            # 1. 날짜 추출
            date_match = re.search(r"(\d{4}[-./]\d{1,2}[-./]\d{1,2})", text)
            if date_match:
                try:
                    date_str = date_match.group(1).replace(".", "-").replace("/", "-")
                    result["purchased_at"] = datetime.strptime(
                        date_str,
                        "%Y-%m-%d"
                    ).date().isoformat()
                except ValueError:
                    pass
            # print(f"--- 1. 추출된 날짜: [{result['purchased_at']}]")
            
            # 2. 업체명 추출 (상호 또는 예금주 옆의 이름)
            supplier_match = re.search(r"(?:상호|예금주)\s*:\s*(\(주\)[가-힣A-Za-z\s]+)", text)
            if supplier_match:
                result["supplier"] = supplier_match.group(1).strip()
                
            else:
                result["supplier"] = "검출에러"
                     
            # print(f"--- 2. 추출된 업체명: [{result['supplier']}]")
            
            # 3. 대표자명(성명) 추출
            name_match = re.search(r"성명\s*([가-힣]{2,})", text)
            if name_match:
                result["representative"] = name_match.group(1).strip()
            else:
                result["representative"] = ""
                
            # print(f"--- 3. 추출된 대표자명: [{result.get('representative', '')}]")

            # 4. 연락처 추출 (TEL)
            tel_match = re.search(r"TEL\s*([0-9\-]{7,})", text)
            if tel_match:
                result["contact"] = tel_match.group(1).strip()
            else:
                result["contact"] = ""
                
            # print(f"--- 4. 추출된 연락처: [{result.get('contact', '')}]")
            
            # 5. 주소 추출 (주소 이후 텍스트 + 다음 줄 병합)
            lines = text.splitlines()
            for i, line in enumerate(lines):
                if "주소" in line:
                    # "주소" 이후 텍스트만 추출
                    after = line.split("주소", 1)[-1].strip()
                    next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                    result["address"] = after + " " + next_line
                    break

            # print(f"--- 5. 추출된 주소: [{result.get('address', '')}]")

            
            # 6. 사업자등록번호 추출
            biz_match = re.search(r"\b\d{3}-\d{2}-\d{5}\b", text)
            if biz_match:
                result["business_number"] = biz_match.group(0).strip()
            else:
                result["business_number"] = ""
                
            # print(f"--- 6. 추출된 사업자등록번호: [{result.get('business_number', '')}]")

            # 표 추출 단계 (items) - 최종 인덱스 및 단위 추출 적용
            # print("--- 7. 표 추출 로직 시작 ---") 
            
            for page in pdf.pages:
                tables = page.extract_tables()
                
                for table in tables:
                    
                    for i, row in enumerate(table):
                        
                        # 품목 데이터가 포함된 행만 처리 (인덱스 6부터 13까지)
                        if not (6 <= i <= 13): 
                            continue 
                            
                        if not row or len(row) < 16: 
                            continue
                            
                        # 품목명(2), 수량(10), 단가(13), 공급가액(15)
                        name = (row[2] or "").strip()
                        for word in REMOVE_WORDS:
                            name = name.replace(word, "")
                        
                        if not name or '품목명' in name or name in ['일자', '']:
                            continue
                            
                        try:
                            # 1. 원본 데이터 추출
                            quantity_raw = row[10] or "0"
                            unit_price_raw = row[13] or "0"
                            supply_raw = row[15] or "0"
                            vat_raw = "0"

                            # 2. 단위 추출 (수량 문자열에서 숫자 외의 문자열 추출)
                            # '0.328kg' -> 'kg' 추출
                            unit_match = re.search(r"\d+(?:\.\d+)?\s*([가-힣a-zA-Z]+)", quantity_raw)
                            unit = unit_match.group(1).strip() if unit_match else ""

                            # 3. 데이터 정제 및 변환
                            quantity = float(re.sub(r"[^0-9.]", "", quantity_raw)) 
                            unit_price = int(re.sub(r"[^0-9]", "", unit_price_raw))
                            supply = int(re.sub(r"[^0-9]", "", supply_raw))
                            vat = int(re.sub(r"[^0-9]", "", vat_raw))
                            
                            result["items"].append({
                                "name": name,
                                "quantity": quantity,
                                "unit": unit, # 새로운 'unit' 필드 추가
                                "unit_price": unit_price,
                                "supply": supply,
                                "vat": vat,
                            })
                            # print(f"--- 품목 추가: {name}, 단위: {unit} ---")
                            
                        except Exception as inner_e:
                            print(f"--- 데이터 변환 오류: {inner_e} - 행 데이터: {row} ---")
                            continue
            
            # print("--- 7. 파싱 로직 완료 및 결과 반환 ---")
            # print(result)

        return result
    
    except Exception as e:
        print(f"--- PDF 파싱 중 치명적인 오류 발생: {e} ---") 
        raise