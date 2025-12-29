# 🌊 Lekker Find

> **Your local plug for Cape Town.**  
> A vibe-based recommendation engine that helps you discover something lekker in under 60 seconds.

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://lekker-find.co.za)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.6-blue)](https://www.typescriptlang.org/)
[![React](https://img.shields.io/badge/React-18.3-61dafb)](https://reactjs.org/)

---

## 📖 About

**Lekker Find** is not your typical venue directory. It's a carefully curated collection of **261 hand-picked Cape Town spots** matched to your mood, budget, and whether you're a local or visitor.

### The Problem

- 🗺️ Google Maps overwhelms you with 5,000+ "average" results
- 🏖️ TripAdvisor sends locals to tourist traps
- 🔍 Most apps understand "Pizza" but not "I want something secret and romantic"

### The Solution

Lekker Find uses **AI-powered semantic matching** to understand vibe, not just keywords. Tell us you want "swimming" or "romantic" and we'll find spots that *feel* right, not just match a category.

**No ads. No sign-up. Free, personal, instant.**

---

## ✨ Features

### 🎯 Smart Recommendation Engine
- **Vibe-Based Matching**: Powered by OpenAI embeddings and cosine similarity
- **Two Discovery Modes**:
  - 🎨 **Personalize**: Answer 3 quick questions for tailored results
  - 🎲 **Surprise Me**: Instant random recommendations with enforced diversity

### 🌍 Local Intelligence
- **Persona Modes**: Different experiences for Locals, Explorers, and Tourists
- **Budget-Aware**: Filter by Free, R, RR, or RRR price tiers with **real prices in ZAR, EUR, USD**
- **Real Prices**: Multi-currency support with real-time exchange rates

### 🎨 Premium User Experience
- **Vibrant Cape Town Aesthetic**: Inspired by ocean sunsets and Table Mountain
- **Smooth Animations**: Built with Framer Motion for delightful micro-interactions
- **Responsive Design**: Mobile-first, works beautifully on all devices
- **Offline-Ready**: All processing happens client-side - works with zero signal

### 🏷️ 15 Curated Vibe Tags
Choose from mood, setting, crowd, and budget vibes:
- **Mood**: Chill · Lively · Romantic · Authentic · Unique
- **Setting**: Nature · Ocean · Indoors · Views
- **Crowd**: Date Night · Group Fun · Solo · Family
- **Money**: Cheap Eat · Boujee

---

## 🛠️ Tech Stack

### Frontend
- **⚛️ React 18.3** - UI library
- **📘 TypeScript 5.6** - Type safety
- **⚡ Vite 6.0** - Lightning-fast build tool
- **🎭 Framer Motion 11** - Smooth animations
- **🎨 Vanilla CSS** - Custom design system with premium utilities

### Data & AI
- **🤖 OpenAI Embeddings** (`text-embedding-3-small`)
- **📊 Matryoshka Optimization** - 256-dim truncated embeddings (83% size reduction)
- **🔢 Cosine Similarity** - Client-side vector matching
- **💱 ECB Exchange Rates** - Real-time currency conversion

### Development
- **🔧 ESLint** - Code quality
- **📦 npm** - Package management

---

## 🚀 Quick Start

### Prerequisites
- Node.js 18+ and npm

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/lekker-find.git
cd lekker-find

# Install dependencies
npm install

# Start development server
npm run dev
```

Visit `http://localhost:5173` to see the app in action! 🎉

### Build for Production

```bash
# Create optimized production build
npm run build

# Preview production build locally
npm run preview
```

---

## 📁 Project Structure

```
lekker-find/
├─ src/
│  ├─ components/
│  │  └─ ui/
│  │     ├─ LoadingScreen.tsx      # Animated loading with SA personality
│  │     └─ RainbowButton.tsx      # Premium gradient CTA button
│  ├─ data/
│  │  ├─ vibes.ts                  # 15 curated vibe tags
│  │  └─ loadingWords.ts           # SA-flavored loading messages
│  ├─ lib/
│  │  └─ utils.ts                  # Utility functions (classNames, etc.)
│  ├─ App.tsx                      # Main application component
│  ├─ index.css                    # Design system & utilities
│  └─ main.tsx                     # React entry point
├─ public/
│  ├─ images/                      # Venue images (static)
│  └─ logo.png                     # App logo
├─ .agent/
│  └─ rules/                       # AI agent build rules
├─ package.json
├─ tsconfig.json
├─ vite.config.ts
└─ README.md
```

---

## 🎨 Design Philosophy

### Voice & Tone
Friendly, local, slightly cheeky. Like a mate who knows every spot in the city.

### Loading Messages
- *"Yoh, checking what's lekker for you…"*
- *"Asking the car guard for advice…"*
- *"Waiting for the mist to clear…"*

### Color Palette
Inspired by Cape Town's natural beauty:
- **Ocean Blues** - `#0891b2`, `#06b6d4`
- **Sunset Orange** - `#f97316`
- **Table Mountain Slate** - `#475569`
- **Golden Hour** - `#fbbf24`

### Typography
Modern, clean, and readable with **Inter** font family.

---

## 🧠 How It Works

### Algorithm Overview

All processing is **100% client-side JavaScript**. No server calls for recommendations.

#### Personalize Flow
1. **Filter** - Remove spots that don't match budget or persona
2. **Match** - Average selected tag vectors to create "target vibe"
3. **Compare** - Calculate cosine similarity between target and all venues
4. **Rank** - Sort by match score, return top 20 results

#### Surprise Me Flow
1. Shuffle all 261 spots
2. Sample 10 with diversity constraints:
   - At least 2 categories represented
   - Mix of price tiers
   - Mix of tourist levels (local gems + popular spots)
3. Return in random order

### Persona Intelligence

| Persona | Behavior |
|---------|----------|
| **Local** | Hides tourist traps (Tourist_Level > 7) |
| **Tourist** | Boosts famous spots in ranking |
| **Explorer** | Shows everything, no filtering |

---

## 📊 The Dataset

**261 curated Cape Town experiences** across:

### Categories
- 🍽️ **Food** - 91 spots (35%)
- 🎯 **Activity** - 45 spots (17%)
- 🌿 **Nature** - 44 spots (17%)
- 🍹 **Drink** - 41 spots (16%)
- 🎭 **Culture** - 40 spots (15%)

### Price Tiers
- 💚 **Free** - 49 spots
- 💰 **R (Budget)** - 99 spots
- 💰💰 **RR (Mid-range)** - 81 spots
- 💰💰💰 **RRR (Premium)** - 32 spots

### Tourist Levels (1-10 scale)
- **1-2**: True local secrets (13 spots)
- **6-7**: Popular but not over-touristed (116 spots, 44%)
- **8-10**: Well-known attractions (54 spots)

---

## 🔮 Roadmap

### ✅ Phase 1: Complete
- [x] Design system implementation
- [x] Questionnaire flow (Persona → Budget → Vibe selection)
- [x] Multi-currency support with real exchange rates
- [x] Premium UI components (RainbowButton, LoadingScreen)
- [x] Responsive mobile-first design

### 🚧 Phase 2: In Progress
- [ ] AI recommendation engine integration
- [ ] Results display with card flipping
- [ ] "Surprise Me" random mode
- [ ] Image integration

### 🎯 Phase 3: Planned
- [ ] PWA support for offline usage
- [ ] Analytics integration (Vercel Analytics)
- [ ] Lighthouse optimization (target: >90)
- [ ] Domain setup: `lekker-find.co.za`

### 🔮 Future Enhancements
- **v1.1**: Google Maps integration ("Go" button)
- **v1.2**: Community suggestion form
- **v2.0**: Save favorites, share results

---

## 🎓 Technical Highlights

This project showcases:

### Frontend Engineering Excellence
- ✨ **Advanced React Patterns**: Custom hooks, component composition
- 🎨 **Premium CSS**: Glassmorphism, gradients, micro-animations
- 📱 **Responsive Design**: Mobile-first with smooth breakpoints
- ⚡ **Performance**: Sub-second load times, optimized bundle size

### AI & Data Science
- 🤖 **Embedding-Based Search**: Semantic similarity over keyword matching
- 📉 **Dimensionality Reduction**: Matryoshka embeddings (83% smaller)
- 🎯 **Client-Side ML**: No backend required for recommendations
- 🔢 **Vector Mathematics**: Cosine similarity for vibe matching

### Developer Experience
- 📘 **Type Safety**: Full TypeScript coverage
- 🧹 **Code Quality**: ESLint rules, consistent formatting
- 📚 **Documentation**: Comprehensive specs and agent rules
- 🔄 **Version Control**: Git best practices

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👨‍💻 About the Developer

Built with ❤️ by **Markus Sass** as a showcase of modern frontend engineering and AI integration.

This project demonstrates:
- Full-stack thinking (though client-side only)
- Product design sensibility
- Senior frontend engineering skills
- AI/ML integration expertise
- Attention to UX details

---

## 🔗 Links

- **Live Demo**: [lekker-find.co.za](https://lekker-find.co.za) *(coming soon)*
- **Portfolio**: [Your Portfolio URL]
- **LinkedIn**: [Your LinkedIn]
- **Email**: [Your Email]

---

## 🙏 Acknowledgments

- **OpenAI** - For embedding models
- **Cape Town** - For being inspirational
- **The 261 venues** - For making CT lekker

---

<div align="center">

**[⬆ back to top](#-lekker-find)**

Made with 🌊 in Cape Town

</div>
