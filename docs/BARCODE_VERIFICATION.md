# Barcode Verification Module

## Overview
The Barcode Verification module is an AI-powered feature that helps users verify the authenticity of pharmaceutical products by analyzing barcodes and QR codes.

## Features

### Input Methods
1. **Image Upload**: Users can upload photos of barcodes/QR codes from product packaging
2. **Manual Entry**: Users can manually enter barcode strings or registration codes

### Verification Process
1. **Barcode Detection**: Automatically detects and decodes barcodes/QR codes from images using OpenCV and pyzbar
2. **Format Validation**: Validates barcode checksums for:
   - EAN-13
   - EAN-8
   - UPC-A
   - Code128
   - QR codes

3. **Database Cross-checking**: Queries two authoritative sources:
   - **PharmAgency API**: Official pharmaceutical pricing and registration database
   - **UzPharm-Control API**: Uzbekistan pharmaceutical control registry

4. **Confidence Scoring**: Calculates a confidence score (0.0-1.0) based on:
   - Barcode validity (30%)
   - PharmAgency database match (30%)
   - UzPharm-Control database match (30%)
   - Price information availability (10%)

### Output
- **Authenticity Label**: 
  - ✅ Genuine (confidence ≥ 70%)
  - ❓ Unknown (confidence 40-70%)
  - ❌ Counterfeit (confidence < 40%)
- **Confidence Score**: Percentage showing verification certainty
- **Explanation**: Detailed reasons for the verdict
- **Recommendation**: Action to take based on the result
- **Product Details**: Name, manufacturer, price (when available)

## Usage

### Access
1. Open the bot and go to the main menu
2. Click "🤖 AI konsultatsiya" (AI Consultation)
3. Click "🔍 Barcode tekshirish" (Barcode Verification)

### Verify a Product
#### Method 1: Upload Image
1. Click "📷 Rasm yuklash" (Upload Image)
2. Take or select a clear photo of the barcode/QR code
3. Send the image to the bot
4. Wait for analysis results

#### Method 2: Enter Code Manually
1. Click "🔢 Kod kiritish" (Enter Code)
2. Type the barcode number or registration code
3. Send the code
4. Wait for verification results

## Security Features

### Input Validation
- **File Size Limit**: 10 MB maximum
- **File Type**: Only image files accepted for photo uploads
- **Timeout Protection**: 30-second timeout for API requests
- **Error Handling**: Graceful handling of network errors and API failures

### Privacy
- Images are processed in memory and not stored permanently
- No personal data is collected during verification
- All communications are encrypted via Telegram's secure protocol

## Technical Details

### Dependencies
- `opencv-python-headless`: Image processing
- `pyzbar`: Barcode decoding
- `pillow`: Image handling
- `requests`: API communication

### APIs Used
1. **PharmAgency API**
   - Endpoint: `https://api.pharmagency.uz/drug-catalog-api/v2/referent-price/all`
   - Purpose: Reference pricing and registration data

2. **UzPharm-Control API**
   - Endpoint: `https://www.uzpharm-control.uz/registries/api_mpip/server-response.php`
   - Purpose: Official pharmaceutical registry

### Supported Barcode Formats
- EAN-13 (International Article Number)
- EAN-8 (Short form)
- UPC-A (Universal Product Code)
- Code128 (Alphanumeric)
- QR Code (2D barcodes)
- DataMatrix (when detectable by pyzbar)

## Limitations

1. **Image Quality**: Clear, well-lit photos work best
2. **API Availability**: Requires internet connection and API availability
3. **Database Coverage**: Only products registered in Uzbekistan databases are verifiable
4. **Barcode Types**: Some specialized formats may not be supported

## Error Handling

### Common Issues and Solutions

**"❌ Rasmda barcode topilmadi"** (No barcode found)
- Solution: Take a clearer photo with better lighting
- Ensure the barcode is fully visible and in focus

**"⚠️ Rasm hajmi juda katta"** (Image too large)
- Solution: Compress or resize the image to under 10 MB

**"❌ Kod tekshirishda xatolik"** (Error during verification)
- Solution: Check internet connection and try again
- Verify the code format is correct

## Future Enhancements

Potential improvements for future versions:
1. OCR for extracting product name, batch, expiry from packaging
2. Integration with additional international databases
3. Blockchain verification for supply chain tracking
4. User reporting system for suspicious products
5. Multi-language support for labels
6. Historical verification tracking

## Support

For issues or questions about the Barcode Verification module, please:
1. Check the bot's help section
2. Contact the support team via the bot
3. Report bugs through the GitHub issue tracker
