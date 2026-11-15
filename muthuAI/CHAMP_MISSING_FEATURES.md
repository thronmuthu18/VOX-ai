# CHAMP — Missing Features & Scope Limitations

This document lists capabilities that are currently outside the scope of the core native desktop assistant or require external services.

---

## 1. Scope Limitations & External Dependencies

### 1. WhatsApp End-to-End Headless Delivery Without QR Login
- **Current Capability**: Opens WhatsApp Web / Protocol, validates phone number format, prepares message, and checks session status.
- **Limitation**: WhatsApp requires an active authenticated web session or QR code scan from a mobile phone. Autonomous message transmission cannot bypass WhatsApp's encryption and device pairing.
- **Requirement**: User must scan QR code in browser once per device to maintain an active session.

### 2. Autonomous Financial & Payment Checkout
- **Current Capability**: Navigates shopping sites (e.g. Flipkart / Amazon) up to product selection and cart view.
- **Limitation**: Real credit card payment, UPI PIN entry, and OTP verification are strictly blocked by the `PolicyEngine` for safety.
- **Requirement**: User must complete the final payment step manually.

### 3. Native Live Video Vision & Camera Analysis
- **Current Capability**: Captures full-screen screenshots via `take_screenshot` for desktop context.
- **Limitation**: Real-time webcam video stream analysis (e.g. recognizing real-world physical objects in front of the camera) is not yet wired into the main voice loop.
- **Requirement**: OpenCV / PyAV live camera stream worker integrated into multimodal Gemini reasoning.

### 4. Background Long-Running Headless Task Daemon (Service Mode)
- **Current Capability**: Interactive terminal voice assistant loop.
- **Limitation**: Does not currently install as a headless Windows Background Service (`services.msc`).
- **Requirement**: Windows Service wrapper (`pywin32` / `nssm`) for system startup without a logged-in user session.
