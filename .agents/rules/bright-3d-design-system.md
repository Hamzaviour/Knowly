---
description: Design system rules and guidelines for Knowly Bright 3D Theme and UI/UX
globs: ["frontend/src/**/*"]
always_on: true
---

# Knowly Bright 3D Design System Guidelines

## Core Principles
1. **Luminous Bright Canvas**:
   - Base background: `#f8fafc` (Slate 50) with subtle mesh gradients (`linear-gradient(135deg, #eef2ff 0%, #f0f9ff 50%, #faf5ff 100%)`).
   - Cards and containers: Pure crisp white (`#ffffff`) with subtle translucent glass borders (`rgba(226, 232, 240, 0.8)`).
   - High contrast, razor-sharp slate typography (`#0f172a` for headings, `#475569` for body, `#64748b` for captions).

2. **3D Tactile & Elevation System**:
   - Multi-layered box shadows for realistic light refraction (`box-shadow: 0 10px 30px -10px rgba(99, 102, 241, 0.08), 0 4px 6px -2px rgba(15, 23, 42, 0.03), inset 0 1px 0 rgba(255, 255, 255, 1)`).
   - 3D lift on hover (`transform: translateY(-2px) scale(1.005)`).
   - Tactile active press feel on interactive buttons (`transform: translateY(1px)`).

3. **Consistent Harmonious Palette**:
   - Primary Brand: Electric Indigo (`#4f46e5`, `#6366f1`)
   - Secondary Accent: Cyan / Sky Blue (`#0284c7`, `#06b6d4`) & Vibrant Purple (`#8b5cf6`)
   - Success: Emerald Green (`#059669`, `#10b981`)
   - Warning / Accent: Warm Amber (`#d97706`, `#f59e0b`)
   - Danger: Coral Rose (`#e11d48`, `#f43f5e`)

4. **Component Consistency**:
   - All pages use `AppLayout` with live backend health monitor, 3D plan badge, and 3D sidebar.
   - Interactive feedback: micro-animations, loading shimmers, 3D pulse beacons.
