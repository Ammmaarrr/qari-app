# Frontend Design System

## Purpose

The `frontend-design/` directory is a **web-based design system and UI prototyping tool** for the Qari App project. It serves as a visual development environment separate from the production mobile app.

## What It Is

- **Technology**: Vite + React + TypeScript
- **Port**: Runs on `http://localhost:3001`
- **Purpose**: Design exploration, component prototyping, and UI/UX testing

## What It's NOT

❌ **Not** the production mobile application (that's in `mobile/`)  
❌ **Not** deployed to end users  
❌ **Not** part of the backend infrastructure

## Use Cases

### 1. **UI Component Prototyping**
Rapidly prototype mobile UI components in the browser before implementing them in React Native.

### 2. **Design Review**
Share design iterations with team members and stakeholders via web browser without needing mobile device setup.

### 3. **Color Scheme Testing**
Experiment with color palettes, typography, and theming before finalizing mobile designs.

### 4. **Animation Previews**
Test animations and transitions in the browser before porting to React Native Reanimated.

### 5. **API Integration Testing**
Test backend API integration flows without mobile emulator/device.

## Directory Structure

```
frontend-design/
├── src/
│   ├── components/     # Reusable UI components (design previews)
│   ├── pages/          # Page mockups
│   ├── styles/         # CSS/design tokens
│   └── utils/          # Design utilities
├── package.json
├── vite.config.ts
└── README.md
```

## Running the Design System

```bash
cd frontend-design
npm install
npm run dev
```

Access at: `http://localhost:3001`

## Relationship to Mobile App

**Design Flow**:
1. Create/test UI in `frontend-design/` (web)
2. Finalize design decisions
3. Implement in `mobile/` (React Native)
4. Deploy to iOS/Android

## When to Use

✅ **Use frontend-design for**:
- Quick visual experimentation
- Stakeholder design reviews
- Responsive layout testing
- Color/theme exploration

✅ **Use mobile/ for**:
- Production code
- Native features (camera, audio recording)
- App store deployment
- End-user functionality

## Deployment

**This design system should NOT be deployed to production.** It is a development tool only.

If you need web access for demos:
- Deploy to internal staging only
- Password protect
- Add "DESIGN PREVIEW - NOT PRODUCTION" watermark

## Team Workflow

1. **Designers**: Create mockups in frontend-design
2. **Review**: Team reviews via localhost or staging
3. **Approve**: Design decisions finalized
4. **Implement**: Developers build in mobile/
5. **Archive**: Design prototypes kept for reference

---

**Status**: Active development tool, not for production deployment.
