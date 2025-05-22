from flask import Flask, request, jsonify
import easyocr
import re
import cv2
import numpy as np
from datetime import datetime

app = Flask(__name__)

reader = easyocr.Reader(['fr'])

def preprocess_image(image_bytes):
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    denoised = cv2.fastNlMeansDenoising(gray)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(denoised)
    _, buffer = cv2.imencode('.jpg', enhanced)
    return buffer.tobytes()

def extract_moroccan_id_info(text_results):
    full_text = ' '.join([item.upper() for item in text_results])
    info = {
        'card_type': None,
        'full_name': None,
        'first_name': None,
        'last_name': None,
        'id_number': None,
        'date_of_birth': None,
        'place_of_birth': None,
        'nationality': None,
        'gender': None,
        'expiry_date': None,
        'issue_date': None,
        'address': None,
        'raw_text': text_results
    }

    if any(keyword in full_text for keyword in ['ROYAUME DU MAROC', 'المملكة المغربية']):
        info['card_type'] = 'Moroccan National ID'

    id_patterns = [r'\b[A-Z]{1,2}\d{6,8}\b', r'\b\d{8}\b', r'\bU\d{7}\b', r'\b[A-Z]\d{6}\b']
    for pattern in id_patterns:
        match = re.search(pattern, full_text)
        if match:
            info['id_number'] = match.group()
            break

    date_patterns = [r'\b\d{2}[/-]\d{2}[/-]\d{4}\b', r'\b\d{2}\.\d{2}\.\d{4}\b', r'\b\d{4}[/-]\d{2}[/-]\d{2}\b']
    dates_found = []
    for pattern in date_patterns:
        matches = re.findall(pattern, full_text)
        dates_found.extend(matches)

    for date_str in dates_found:
        for fmt in ['%d/%m/%Y', '%d-%m-%Y', '%d.%m.%Y', '%Y/%m/%d', '%Y-%m-%d']:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                current_year = datetime.now().year
                if 1930 <= date_obj.year <= 2010:
                    info['date_of_birth'] = date_str
                elif date_obj.year > current_year:
                    info['expiry_date'] = date_str
                elif current_year - 10 <= date_obj.year <= current_year:
                    info['issue_date'] = date_str
                break
            except ValueError:
                continue

    name_candidates = []
    for item in text_results:
        item_clean = item.strip()
        if re.search(r'\d', item_clean) or len(item_clean) < 2:
            continue
        skip_words = ['ROYAUME', 'MAROC', 'CARTE', 'NATIONALE', 'IDENTITE', 
                     'SPECIMEN', 'VALABLE', 'JUSQU', 'NE', 'A', 'LE']
        if not any(word in item_clean.upper() for word in skip_words):
            name_candidates.append(item_clean)

    if name_candidates:
        filtered_names = [name for name in name_candidates if len(name) > 3]
        if filtered_names:
            info['full_name'] = max(filtered_names, key=len)
            name_parts = info['full_name'].split()
            if len(name_parts) >= 2:
                info['first_name'] = name_parts[0]
                info['last_name'] = ' '.join(name_parts[1:])

    if any(word in full_text for word in ['M', 'MASCULIN']):
        info['gender'] = 'Male'
    elif any(word in full_text for word in ['F', 'FEMININ']):
        info['gender'] = 'Female'

    moroccan_cities = [
        # Major Cities
        'CASABLANCA', 'RABAT', 'FES', 'MARRAKECH', 'AGADIR',
        'TANGIER', 'MEKNES', 'OUJDA', 'KENITRA', 'TETOUAN',
        'SALE', 'TEMARA', 'MOHAMMEDIA', 'KHOURIBGA', 'JADIDA',
        'OUARZAZATE', 'SAFI', 'BENI MELLAL', 'EL JADIDA', 'TAZA',
        'NADOR', 'LARACHE', 'KSAR EL KEBIR', 'ERRACHIDIA', 'TAROUDANT',
        'BERKANE', 'SIDI KACEM', 'TAOURIRT', 'GUELMIM', 'TIZNIT',
        'TIFLET', 'YOUSSOUFIA', 'MIDELT', 'SIDI SLIMANE', 'SEFROU',
        'AZROU', 'DEMNATE', 'BOUJDOUR', 'TAN-TAN', 'FIGUIG',
        'ASILAH', 'CHEFCHAOUEN', 'DRIOUCH', 'ZAGORA', 'TINGHIR',
        'SMARA', 'LAAYOUNE', 'DAKHLA', 'BOUDNIB', 'IFRANE',
        
        # Smaller Towns & Notable Locations
        'ESSAOUIRA', 'KHENIFRA', 'SIDI IFNI', 'BERRECHID', 'SKHIRAT',
        'AIN HARROUDA', 'BOUZNIKA', 'SIDI BENNOUR', 'FQUIH BEN SALAH',
        'SOUK EL ARBAA', 'OUED ZEM', 'SIDI YAHYA ZAER', 'BOUARFA',
        'TARFAYA', 'AKKA', 'TATA', 'OULAD TEIMA', 'SIDI BOUZID',
        'BIR LEHLU', 'AIT MELLOUL', 'INEZGANE', 'DRARGUA', 'BIOUGRA',
        'CHICHAOUA', 'EL KELAA DES SRAGHNA', 'BEN GUERIR', 'YOUSSOUFIA',
        'SIDI RAHHAL', 'AMIZMIZ', 'ASNI', 'IMLIL', 'OUIRGANE',
        'TAMANAR', 'SIDI KAOUKI', 'TAMRI', 'TAGHAZOUT', 'AOURIR',
        'BELFAA', 'TIZNIT', 'TAFRAOUT', 'MIRLEFT', 'SIDI BOUATI',
        'SIDI BOUKNADEL', 'MEHDYA', 'MOUNA', 'SIDI ALLAL EL BAHRAOUI',
        'SIDI SLIMANE', 'SIDI TAIBI', 'SIDI YAHYA EL GHARB', 'SIDI BETTACHE',
        'SIDI BOUGHAABA', 'SIDI HARAZEM', 'VOLUBILIS', 'MOULAY IDRISS',
        'SIDI KERKOUM', 'SIDI ALI BEN HAMDOUCHE', 'SIDI CHAMHAROUCH',
        'SIDI IFNI', 'SIDI MOUSSA', 'SIDI BOU OTHMANE', 'SIDI BOUNAMANE',
        'SIDI BOUZID', 'SIDI DAOUD', 'SIDI EL AIDI', 'SIDI HAJJAJ',
        'SIDI HRAZEM', 'SIDI MOHAMED BEN ABDELLAH', 'SIDI RAHHAL CHATAI',
        'SIDI SMAIL', 'SIDI YAHYA OU SAAD', 'SIDI YAHYA DES ZAERS',
        'SIDI ZOUINE', 'SIDI ABDELLAH', 'SIDI ABDELLAH BEN MBAREK',
        'SIDI ALI BOUGHALEB', 'SIDI ALI LAGHDARI', 'SIDI ALLAL TAZI',
        'SIDI BOUKNADEL', 'SIDI BOURHABA', 'SIDI BRAHIM', 'SIDI BOUZID',
        'SIDI DAOUDI', 'SIDI EL HATTAB', 'SIDI HAMZA', 'SIDI HARAZEM',
        'SIDI HAZEM', 'SIDI HSSAIN', 'SIDI KACEM', 'SIDI LAHCEN',
        'SIDI LYAMANI', 'SIDI MOHAMED BEN YOUSSEF', 'SIDI MOHAMED LAHMER',
        'SIDI MOUMEN', 'SIDI MOUSTAFA', 'SIDI RAHHAL', 'SIDI RAHHAL EL GHAZOUANI',
        'SIDI SLIMANE', 'SIDI SMAIL', 'SIDI TAIBI', 'SIDI YAHIA',
        'SIDI YAHYA EL GHARB', 'SIDI YOUSSEF BEN AHMED', 'SIDI ZOUINE',
        
        # Sahara & Southern Regions
        'BOJADOR', 'LAGOUIRA', 'BIR ANZARANE', 'MAHDIA', 'FAM EL HISN',
        'GUELTA ZEMMUR', 'OUED EDDAHAB', 'AOUSSERD', 'BIR GANDOUZ',
        'TICHLA', 'ZOUERAT', 'AIN BENI MATHAR', 'BOUANANE', 'TALSINNT',
        'AKHFENNIR', 'TARFAYA', 'LAMSSID', 'LABOUIRAT', 'LEGUIRA',
        'BIR ENZARAN', 'AMGALA', 'HAWZA', 'TICHLA', 'BOUKRAA',
        'TINDOUF', 'TINJIDAD', 'TINZOULINE', 'TISSINT', 'TIZI NISLY',
        'TIZI OUSSEMI', 'TIZOUGHRINE', 'TIZI NTLATA', 'TIZI RACHED',
        'TIZI NCHTKA', 'TIZI OUAGANE', 'TIZI OUADOU', 'TIZI OUMALOU',
        'TIZI OUGHRANE', 'TIZI OULOUZ', 'TIZI RHELISSA', 'TIZI TGHEST',
        'TIZI TCHTKA', 'TIZI NTERGA', 'TIZI OUADOU', 'TIZI OUAGLAM',
        'TIZI OUADOU', 'TIZI OUADOU', 'TIZI OUADOU', 'TIZI OUADOU',
        
        # Northern & Rif Region
        'AL HOCEIMA', 'NADOR', 'TAOURIRT', 'BERKANE', 'DRIOUCH',
        'OUAZZANE', 'TARGUIST', 'BAB BERRED', 'BAB TAZA', 'BENI ANSAR',
        'BENI CHIKAR', 'BENI HADIFA', 'BENI SIDEL', 'BENI SIDEL JEBEL',
        'BENI BOUAYACH', 'BENI BOUFRAH', 'BENI BOUZRA', 'BENI DERKOUL',
        'BENI ENSAR', 'BENI GMIL', 'BENI GMILA', 'BENI GUIL', 'BENI HARCHEM',
        'BENI HOUNK', 'BENI KHIAR', 'BENI LECHKER', 'BENI MALIK',
        'BENI MARGHINE', 'BENI MEZALA', 'BENI MHAMMED', 'BENI OULID',
        'BENI OURIAGHEL', 'BENI SAID', 'BENI SIDEL', 'BENI SMIR',
        'BENI TADJIT', 'BENI TIZI', 'BENI TOUZINE', 'BENI YAKHLEF',
        'BENI YENNI', 'BENI ZRANTEL', 'BENI ZRANTEL', 'BENI ZRANTEL',
    ]
    for city in moroccan_cities:
        if city in full_text:
            info['place_of_birth'] = city.title()
            break

    if any(word in full_text for word in ['MAROCAINE']):
        info['nationality'] = 'Moroccan'

    return info

@app.route('/ocr', methods=['POST'])
def ocr_endpoint():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image = request.files['image']
    image_bytes = image.read()

    try:
        processed_image = preprocess_image(image_bytes)
        result = reader.readtext(processed_image, detail=0, paragraph=False)
        info = extract_moroccan_id_info(result)
        return jsonify({'success': True, 'data': info})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'service': 'Moroccan ID OCR Scanner'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
