import { useState, useMemo, useEffect, lazy, Suspense } from 'react';
import { LazyMotion, domAnimation, m, AnimatePresence } from 'framer-motion';
import {
    Sparkles, Gem, ChevronRight, ArrowLeft,
    Camera, Star, Heart, Scale,
    UtensilsCrossed, Mountain, TreePine, Coffee, Landmark,
    Gift, Coins, Banknote, Crown, Shuffle, RefreshCcw
} from 'lucide-react';

import { RainbowButton } from './components/ui/RainbowButton';
// Lazy load heavy components
const LoadingScreen = lazy(() => import('./components/ui/LoadingScreen').then(module => ({ default: module.LoadingScreen })));
const SwipeableResults = lazy(() => import('./components/ui/SwipeableResults').then(module => ({ default: module.SwipeableResults })));
import { getContextualMoods, shouldShowPriceDisclaimer, getBudgetDisplay } from './data/vibes';
import { useRecommendations, VenueWithMatch } from './utils/matcher';


/**
 * Lekker Find App
 * 
 * A premium, Apple-inspired app for discovering Cape Town experiences.
 * Multi-step flow: Landing → Intent → Tourist Level → Budget → Mood → Results
 * 
 * SEO: Optimized for "best things to do in Cape Town" and related queries.
 * Accessibility: Uses clear, simple language for diverse audiences.
 */

type AppStep = 'landing' | 'question-intent' | 'question-vibe' | 'question-budget' | 'question-mood' | 'results';

// Intent options - simple, action-oriented wording
const intentOptions = [
    { value: 'food', label: 'Eat', sublabel: 'Food & restaurants', icon: UtensilsCrossed },
    { value: 'drink', label: 'Drink', sublabel: 'Coffee, wine & bars', icon: Coffee },
    { value: 'activity', label: 'Do', sublabel: 'Fun activities', icon: Mountain },
    { value: 'nature', label: 'Explore', sublabel: 'Nature & outdoors', icon: TreePine },
    { value: 'culture', label: 'Discover', sublabel: 'Culture & history', icon: Landmark },
    { value: 'any', label: 'Surprise me', sublabel: 'Anything goes', icon: Sparkles },
];

// Tourist level spectrum - famous spots to hidden gems
const touristLevelOptions = [
    { value: 1, label: 'Famous', sublabel: 'Must-see spots', icon: Camera },
    { value: 2, label: 'Popular', sublabel: 'Well-known picks', icon: Star },
    { value: 3, label: 'Balanced', sublabel: 'Best of both', icon: Scale },
    { value: 4, label: 'Local', sublabel: 'Off the path', icon: Heart },
    { value: 5, label: 'Hidden', sublabel: 'Secret gems', icon: Gem },
];

// Budget options - dynamically shows EUR for tourists
// Budget options - dynamically shows ZAR or EUR based on toggle
// Budget options - dynamically shows ZAR, EUR or USD based on toggle
const getBudgetOptions = (currency: 'ZAR' | 'EUR' | 'USD', rates: Record<string, number>) => [
    { value: 'free', label: 'Free', sublabel: 'No cost', icon: Gift },
    { value: 'budget', label: 'Budget', sublabel: getBudgetDisplay('budget', currency, rates), icon: Coins },
    { value: 'moderate', label: 'Mid-range', sublabel: getBudgetDisplay('moderate', currency, rates), icon: Banknote },
    { value: 'premium', label: 'Premium', sublabel: getBudgetDisplay('premium', currency, rates), icon: Crown },
    { value: 'any', label: 'Any price', sublabel: 'Show all', icon: Shuffle },
];

function App() {
    // Recommendation engine
    const { findMatches, surpriseMe, ready: recommendationsReady } = useRecommendations();

    const [isLoading, setIsLoading] = useState(false);
    const [currentStep, setCurrentStep] = useState<AppStep>('landing');
    const [matchedVenues, setMatchedVenues] = useState<VenueWithMatch[]>([]);

    const [selectedIntent, setSelectedIntent] = useState<string | null>(null);
    const [selectedTouristLevel, setSelectedTouristLevel] = useState<number | null>(null);
    const [selectedBudget, setSelectedBudget] = useState<string | null>(null);
    const [selectedMoods, setSelectedMoods] = useState<string[]>([]);
    const [currency, setCurrency] = useState<'ZAR' | 'EUR' | 'USD'>('ZAR');
    const [exchangeRates, setExchangeRates] = useState<Record<string, number>>({ ZAR: 1, EUR: 0.05, USD: 0.053 });

    const handleCurious = () => {
        // Preset for "Surprise Me" flow
        if (!recommendationsReady) return;
        const results = surpriseMe(20);
        setMatchedVenues(results);
        setSelectedIntent('any');
        setSelectedTouristLevel(3);
        setSelectedBudget('any');
        setSelectedMoods([]);
        setIsLoading(true);
    };

    // Fetch live exchange rates on mount
    useEffect(() => {
        const fetchRates = async () => {
            try {
                // Using open.er-api.com for free, no-key live rates
                const response = await fetch('https://open.er-api.com/v6/latest/ZAR');
                const data = await response.json();
                if (data && data.rates) {
                    setExchangeRates({
                        ZAR: 1,
                        EUR: data.rates.EUR,
                        USD: data.rates.USD
                    });
                }
            } catch (error) {
                console.error('Failed to fetch exchange rates:', error);
                // Fallback rates roughly valid as of late 2024
            }
        };

        fetchRates();

        // --------------------------------------------------------
        // Seamless Hydration Strategy:
        // The HTML Shell (#app-shell) is covering the screen (LCP).
        // React renders the Landing page underneath (isFirstVisit=true sets it to visible).
        // Now we fade out the Shell to reveal the interactive App.
        // --------------------------------------------------------
        const shell = document.getElementById('app-shell');
        if (shell) {
            // Small delay to ensure React has painted
            setTimeout(() => {
                shell.style.opacity = '0';
                shell.style.pointerEvents = 'none';
                setTimeout(() => {
                    shell.remove();
                }, 600); // 600ms matches index.html transition
            }, 100);
        }

    }, []);

    // Show price disclaimer (general variability note)
    const showPriceDisclaimer = shouldShowPriceDisclaimer(selectedIntent, selectedTouristLevel);

    // Budget options adapt based on currency selection
    const budgetOptions = useMemo(
        () => getBudgetOptions(currency, exchangeRates),
        [currency, exchangeRates]
    );

    // Get context-aware moods based on previous selections
    const [availableMoods, setAvailableMoods] = useState<string[]>([]);

    // Update available moods when context changes
    useEffect(() => {
        setAvailableMoods(getContextualMoods(selectedIntent, selectedTouristLevel, selectedBudget, 12));
    }, [selectedIntent, selectedTouristLevel, selectedBudget]);

    // Calculate progress percentage (now 4 steps)
    const getProgress = () => {
        switch (currentStep) {
            case 'question-intent': return 25;
            case 'question-vibe': return 50;
            case 'question-budget': return 75;
            case 'question-mood': return 100;
            default: return 0;
        }
    };

    const getStepNumber = () => {
        switch (currentStep) {
            case 'question-intent': return 1;
            case 'question-vibe': return 2;
            case 'question-budget': return 3;
            case 'question-mood': return 4;
            default: return 0;
        }
    };

    // Page transition variants
    const pageVariants = {
        initial: (custom: { isFirstMount: boolean }) => ({
            opacity: custom.isFirstMount ? 1 : 0,
            y: custom.isFirstMount ? 0 : 20
        }),
        animate: {
            opacity: 1,
            y: 0,
            transition: { duration: 0.5, ease: [0.25, 0.46, 0.45, 0.94] }
        },
        exit: {
            opacity: 0,
            y: -20,
            transition: { duration: 0.3, ease: 'easeIn' }
        }
    };

    // Stagger children animation
    const containerVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                staggerChildren: 0.06,
                delayChildren: 0.1,
            },
        },
    };

    const itemVariants = {
        hidden: { opacity: 0 },
        visible: {
            opacity: 1,
            transition: {
                duration: 0.3,
                ease: 'easeOut',
            },
        },
    };

    const logoVariants = {
        hidden: { opacity: 0, scale: 0.8 },
        visible: {
            opacity: 1,
            scale: 1,
            transition: {
                duration: 0.6,
                ease: [0.25, 0.46, 0.45, 0.94],
            },
        },
    };

    const handleBegin = () => setCurrentStep('question-intent');

    const handleBack = () => {
        if (currentStep === 'question-intent') {
            setCurrentStep('landing');
            setSelectedIntent(null);
        } else if (currentStep === 'question-vibe') {
            setCurrentStep('question-intent');
            setSelectedTouristLevel(null);
        } else if (currentStep === 'question-budget') {
            setCurrentStep('question-vibe');
            setSelectedBudget(null);
        } else if (currentStep === 'question-mood') {
            setCurrentStep('question-budget');
            setSelectedMoods([]);
        }
    };

    const handleIntentSelect = (value: string) => {
        setSelectedIntent(value);
        setTimeout(() => {
            setCurrentStep('question-vibe');
            window.scrollTo(0, 0);
            if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        }, 300);
    };

    const handleTouristLevelSelect = (value: number) => {
        setSelectedTouristLevel(value);
        setTimeout(() => {
            setCurrentStep('question-budget');
            window.scrollTo(0, 0);
            if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        }, 300);
    };

    const handleBudgetSelect = (value: string) => {
        setSelectedBudget(value);
        setTimeout(() => {
            setCurrentStep('question-mood');
            window.scrollTo(0, 0);
            if (document.activeElement instanceof HTMLElement) document.activeElement.blur();
        }, 300);
    };

    const handleMoodToggle = (mood: string) => {
        setSelectedMoods(prev =>
            prev.includes(mood)
                ? prev.filter(m => m !== mood)
                : [...prev, mood]
        );
    };

    const handleMoodContinue = () => {
        if (!recommendationsReady) return;

        // Get matches from recommendation engine
        const results = findMatches({
            intent: selectedIntent,
            touristLevel: selectedTouristLevel,
            budget: selectedBudget,
            moods: selectedMoods,
        }, { minScore: 0.35, maxResults: 20 });

        setMatchedVenues(results);
        setIsLoading(true);
    };

    const handleStartOver = () => {
        setCurrentStep('landing');
        setSelectedIntent(null);
        setSelectedTouristLevel(null);
        setSelectedBudget(null);
        setSelectedMoods([]);
        setMatchedVenues([]);
    };

    // Render a question page
    const renderQuestionPage = (
        title: string,
        subtitle: React.ReactNode,
        options: Array<{ value: string | number; label: string; sublabel: string; icon: React.ComponentType<{ className?: string }> }>,
        selectedValue: string | number | null,
        onSelect: (value: any) => void,
        hint?: string
    ) => (
        <m.article
            className="question-content"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
        >
            {/* Back Button */}
            <m.button
                className="btn-back"
                variants={itemVariants}
                onClick={handleBack}
                whileHover={{ x: -4 }}
                whileTap={{ scale: 0.98 }}
                aria-label="Go back"
            >
                <ArrowLeft className="icon" aria-hidden="true" />
            </m.button>

            {/* Progress Indicator */}
            <m.div className="question-progress" variants={itemVariants}>
                <div className="progress-bar">
                    <m.div
                        className="progress-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${getProgress()}% ` }}
                        transition={{ duration: 0.5, ease: 'easeOut' }}
                    />
                </div>
                <span className="progress-text">{getStepNumber()} of 4</span>
            </m.div>

            {/* Question */}
            <m.h2 className="question-title" variants={itemVariants}>
                {title}
            </m.h2>
            <m.p className="question-subtitle" variants={itemVariants}>
                {subtitle}
            </m.p>

            {/* Options */}
            <m.div
                className="vibeOptionList"
                variants={itemVariants}
            >
                {options.map((option) => {
                    const IconComponent = option.icon;
                    const isSelected = selectedValue === option.value;

                    return (
                        <m.button
                            key={option.value}
                            className={`vibeOptionItem ${isSelected ? 'selected' : ''}`}
                            onClick={() => onSelect(option.value)}
                            whileHover={{ scale: 1.02, y: -2 }}
                            whileTap={{ scale: 0.98 }}
                            aria-pressed={isSelected}
                        >
                            <div className="vibeOptionIcon">
                                <IconComponent aria-hidden="true" />
                            </div>
                            <div className="vibeOptionText">
                                <span className="vibeOptionLabel">{option.label}</span>
                                <span className="vibeOptionSub">{option.sublabel}</span>
                            </div>
                            {isSelected && (
                                <m.div
                                    className="vibeOptionCheck"
                                    initial={{ scale: 0 }}
                                    animate={{ scale: 1 }}
                                    transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                                >
                                    <ChevronRight aria-hidden="true" />
                                </m.div>
                            )}
                        </m.button>
                    );
                })}
            </m.div>

            {/* Optional hint/disclaimer */}
            {
                hint && (
                    <m.p className="question-hint" variants={itemVariants}>
                        {hint}
                    </m.p>
                )
            }
        </m.article >
    );

    const budgetSubtitle = (
        <div className="budgetSubtitleWrapper">
            <span>Per person, roughly</span>
            <div className="currencyToggleContainer">
                <button
                    className={`currencyToggleBtn ${currency === 'ZAR' ? 'active' : ''}`}
                    onClick={() => setCurrency('ZAR')}
                    aria-label="ZAR"
                >
                    R
                </button>
                <div className="currencyDivider" />
                <button
                    className={`currencyToggleBtn ${currency === 'EUR' ? 'active' : ''}`}
                    onClick={() => setCurrency('EUR')}
                    aria-label="EUR"
                >
                    €
                </button>
                <div className="currencyDivider" />
                <button
                    className={`currencyToggleBtn ${currency === 'USD' ? 'active' : ''}`}
                    onClick={() => setCurrency('USD')}
                    aria-label="USD"
                >
                    $
                </button>
            </div>
        </div>
    );

    return (
        <LazyMotion features={domAnimation}>
            {/* JSON-LD Structured Data for SEO & LLM */}
            <script
                type="application/ld+json"
                dangerouslySetInnerHTML={{
                    __html: JSON.stringify([
                        {
                            '@context': 'https://schema.org',
                            '@type': 'WebApplication',
                            name: 'Lekker Find - Best Things to Do in Cape Town',
                            alternateName: 'Lekker Find',
                            description:
                                'Discover the best things to do in Cape Town. 320+ hand-picked hidden gems, date spots, and local favorites. AI-matched to your vibe.',
                            url: 'https://lekker-find.co.za',
                            applicationCategory: 'TravelApplication',
                            operatingSystem: 'Web',
                            offers: {
                                '@type': 'Offer',
                                price: '0',
                                priceCurrency: 'ZAR',
                            },
                            aggregateRating: {
                                '@type': 'AggregateRating',
                                ratingValue: '4.9',
                                reviewCount: '320',
                            },
                            author: {
                                '@type': 'Organization',
                                name: 'Lekker Find',
                                logo: 'https://lekker-find.co.za/logo-min.png'
                            },
                            areaServed: {
                                '@type': 'City',
                                name: 'Cape Town',
                                containedInPlace: {
                                    '@type': 'Country',
                                    name: 'South Africa',
                                },
                            },
                            keywords: 'best things to do in Cape Town, things to do in Cape Town, Cape Town hidden gems, Cape Town date ideas, Cape Town travel guide'
                        },
                        {
                            '@context': 'https://schema.org',
                            '@type': 'FAQPage',
                            mainEntity: [
                                {
                                    '@type': 'Question',
                                    name: 'What are the best things to do in Cape Town?',
                                    acceptedAnswer: {
                                        '@type': 'Answer',
                                        text: 'The best things to do in Cape Town include visiting iconic spots like Table Mountain and Cape Point, as well as exploring hidden gems like secret beaches, local craft markets, and world-class wine estates in Constantia and Stellenbosch. Lekker Find helps you discover 320+ of these hand-picked spots.'
                                    }
                                },
                                {
                                    '@type': 'Question',
                                    name: 'How do I find local recommendations in Cape Town?',
                                    acceptedAnswer: {
                                        '@type': 'Answer',
                                        text: 'Lekker Find provides AI-matched recommendations based on your personal vibe, budget, and interests. Whether you want to eat, drink, or explore, we match you with the best local-approved spots in the Mother City.'
                                    }
                                }
                            ]
                        }
                    ]),
                }}
            />

            <main className="app-container" role="main">
                {/* Background decorative elements */}
                <div className="landing-background" aria-hidden="true" />
                <div className="landing-orb landing-orb-1" aria-hidden="true" />
                <div className="landing-orb landing-orb-2" aria-hidden="true" />

                <AnimatePresence mode="wait">
                    {currentStep === 'landing' && (
                        <m.div
                            key="landing"
                            className="page-wrapper"
                            variants={pageVariants}
                            initial="initial"
                            animate="animate"
                            exit="exit"
                            custom={{ isFirstMount: currentStep === 'landing' }}
                        >
                            {/* Landing Page Content */}
                            <m.article
                                className="landing-content"
                                variants={containerVariants}
                                initial="hidden"
                                animate="visible"
                                itemScope
                                itemType="https://schema.org/WebPage"
                            >
                                <m.header
                                    className="landing-logo"
                                    variants={logoVariants}
                                    aria-label="Lekker Find"
                                >
                                    <img
                                        src="/logo-min.png"
                                        alt="Lekker Find - Best things to do in Cape Town"
                                        className="landing-logo-img"
                                        width="160"
                                        height="160"
                                        decoding="async"
                                        {...{ fetchpriority: "high" } as any}
                                    />
                                </m.header>

                                <m.h1
                                    className="landing-slogan"
                                    variants={itemVariants}
                                    itemProp="headline"
                                >
                                    Discover something{' '}
                                    <span className="landing-slogan-accent">lekker</span>
                                </m.h1>

                                <m.p
                                    className="landing-description"
                                    variants={itemVariants}
                                    itemProp="description"
                                >
                                    Not sure what to do in Cape Town?<br />
                                    Let us help you. Free, personal, instant.
                                </m.p>



                                <m.div className="landing-ctas" variants={itemVariants}>
                                    <m.button
                                        className="btn-get-started"
                                        whileTap={{ scale: 0.98 }}
                                        onClick={handleBegin}
                                        aria-label="Get Started"
                                    >
                                        <div className="btn-get-started-icon-wrapper">
                                            <Sparkles className="icon" aria-hidden="true" />
                                        </div>
                                        Get Started
                                    </m.button>

                                    <m.button
                                        className="btn-secondary-curious"
                                        whileHover={{ scale: 1.02 }}
                                        whileTap={{ scale: 0.98 }}
                                        onClick={handleCurious}
                                        aria-label="Feeling curious? Explore Cape Town randomly"
                                    >
                                        <Shuffle className="icon" aria-hidden="true" />
                                        <span>Feeling curious?</span>
                                    </m.button>

                                </m.div>
                            </m.article>

                            <footer className="landing-footer" role="contentinfo">
                                <p className="landing-footer-text">
                                    <span itemProp="about">
                                        Your local plug for Cape Town · 320+ hand-picked spots
                                    </span>
                                </p>
                            </footer>
                        </m.div>
                    )}

                    {currentStep === 'question-intent' && (
                        <m.div
                            key="question-intent"
                            className="page-wrapper"
                            variants={pageVariants}
                            initial="initial"
                            animate="animate"
                            exit="exit"
                            custom={{ isFirstMount: false }}
                        >
                            {renderQuestionPage(
                                "What are you in the mood for?",
                                "Pick one, or let us surprise you",
                                intentOptions,
                                selectedIntent,
                                handleIntentSelect
                            )}
                        </m.div>
                    )}

                    {currentStep === 'question-vibe' && (
                        <m.div
                            key="question-vibe"
                            className="page-wrapper"
                            variants={pageVariants}
                            initial="initial"
                            animate="animate"
                            exit="exit"
                            custom={{ isFirstMount: false }}
                        >
                            {renderQuestionPage(
                                "What kind of experience?",
                                "From famous attractions to secret local spots",
                                touristLevelOptions,
                                selectedTouristLevel,
                                handleTouristLevelSelect
                            )}
                        </m.div>
                    )}

                    {currentStep === 'question-budget' && (
                        <m.div
                            key="question-budget"
                            className="page-wrapper"
                            variants={pageVariants}
                            initial="initial"
                            animate="animate"
                            exit="exit"
                            custom={{ isFirstMount: false }}
                        >
                            {renderQuestionPage(
                                "What's your budget?",
                                budgetSubtitle,
                                budgetOptions,
                                selectedBudget,
                                handleBudgetSelect,
                                showPriceDisclaimer ? "* Note: Prices are estimates and may vary by season" : undefined
                            )}
                        </m.div>
                    )}

                    {currentStep === 'question-mood' && (
                        <m.div
                            key="question-mood"
                            className="page-wrapper"
                            variants={pageVariants}
                            initial="initial"
                            animate="animate"
                            exit="exit"
                            custom={{ isFirstMount: false }}
                        >
                            <m.article
                                className="question-content"
                                variants={containerVariants}
                                initial="hidden"
                                animate="visible"
                            >
                                {/* Back Button */}
                                <m.button
                                    className="btn-back"
                                    variants={itemVariants}
                                    onClick={handleBack}
                                    whileHover={{ x: -4 }}
                                    whileTap={{ scale: 0.98 }}
                                    aria-label="Go back"
                                >
                                    <ArrowLeft className="icon" aria-hidden="true" />
                                </m.button>

                                {/* Progress Indicator */}
                                <m.div className="question-progress" variants={itemVariants}>
                                    <div className="progress-bar">
                                        <m.div
                                            className="progress-fill"
                                            initial={{ width: 0 }}
                                            animate={{ width: `${getProgress()}% ` }}
                                            transition={{ duration: 0.5, ease: 'easeOut' }}
                                        />
                                    </div>
                                    <span className="progress-text">{getStepNumber()} of 4</span>
                                </m.div>

                                {/* Question */}
                                <m.h2 className="question-title" variants={itemVariants}>
                                    What's the vibe?
                                </m.h2>
                                <m.p className="question-subtitle" variants={itemVariants}>
                                    Pick a few that match your mood
                                </m.p>

                                {/* Mood Tags Multi-select */}
                                <AnimatePresence mode="wait">
                                    <m.div
                                        key={availableMoods.join('-')}
                                        className="moodTagsList"
                                        initial={{ opacity: 0 }}
                                        animate={{ opacity: 1 }}
                                        exit={{ opacity: 0 }}
                                        transition={{ duration: 0.3 }}
                                    >
                                        {availableMoods.map((tag) => {
                                            const isSelected = selectedMoods.includes(tag);
                                            return (
                                                <m.button
                                                    key={tag}
                                                    className={`moodTagItem ${isSelected ? 'selected' : ''}`}
                                                    onClick={() => handleMoodToggle(tag)}
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    transition={{ duration: 0.2 }}
                                                    whileHover={{ scale: 1.05 }}
                                                    whileTap={{ scale: 0.95 }}
                                                    aria-pressed={isSelected}
                                                    aria-label={`Select ${tag} mood`}
                                                >
                                                    {tag}
                                                </m.button>
                                            );
                                        })}
                                    </m.div>
                                </AnimatePresence>

                                {/* Actions */}
                                <m.div
                                    className="moodActions"
                                    variants={itemVariants}
                                    initial="hidden"
                                    animate="visible"
                                >
                                    <button
                                        onClick={() => {
                                            // Keep what is selected, shuffle the rest
                                            const keptMoods = availableMoods.filter(m => selectedMoods.includes(m));
                                            const countNeeded = 12 - keptMoods.length;

                                            if (countNeeded > 0) {
                                                const newMoods = getContextualMoods(
                                                    selectedIntent,
                                                    selectedTouristLevel,
                                                    selectedBudget,
                                                    countNeeded,
                                                    availableMoods // Avoid current list
                                                );

                                                setAvailableMoods([...keptMoods, ...newMoods]);
                                            }
                                        }}
                                        className="btn-shuffle"
                                        aria-label="Shuffle options"
                                    >
                                        <RefreshCcw size={14} aria-hidden="true" />
                                        <span>Shuffle options</span>
                                    </button>
                                </m.div>

                                {/* Generate CTA */}
                                <m.div className="generateActionContainer" variants={itemVariants}>
                                    <RainbowButton
                                        onClick={handleMoodContinue}
                                        disabled={selectedMoods.length === 0}
                                        className={selectedMoods.length === 0 ? "inactive" : ""}
                                        data-excitement={selectedMoods.length > 0 ? selectedMoods.length : 0}
                                    >
                                        Your Suggestions
                                    </RainbowButton>
                                </m.div>
                            </m.article>
                        </m.div>

                    )}
                </AnimatePresence>

                <Suspense fallback={null}>
                    <LoadingScreen
                        isVisible={isLoading}
                        touristLevel={selectedTouristLevel}
                        intent={selectedIntent}
                        venues={matchedVenues}
                        onComplete={() => {
                            setIsLoading(false);
                            setCurrentStep('results');
                        }}
                    />

                    {/* Results View */}
                    {currentStep === 'results' && (
                        <SwipeableResults
                            venues={matchedVenues}
                            onClose={handleStartOver}
                            onStartOver={handleStartOver}
                            currency={currency}
                            exchangeRates={exchangeRates}
                        />
                    )}
                </Suspense>
            </main >
        </LazyMotion>
    );
}

export default App;
