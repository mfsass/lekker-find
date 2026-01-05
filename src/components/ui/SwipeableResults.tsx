/**
 * SwipeableResults - Tinder-style venue cards
 * ==========================================
 * 
 * Full-screen swipeable cards with:
 * - Background image with gradient overlay
 * - Match percentage badge
 * - Venue name, category, price
 * - Description
 * - Open in Maps button
 * - Swipe left/right or tap arrows
 */

import React, { useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence, PanInfo } from 'framer-motion';
import { MapPin, ChevronLeft, ChevronRight, Star, ThumbsUp, ThumbsDown, Sparkles } from 'lucide-react';
import { VenueWithMatch } from '../../utils/matcher';
import { convertPriceString } from '../../utils/currency';
import { getVenueImage } from '../../utils/imageHelper';
import { captureFeedback } from '../../utils/analytics';
import './SwipeableResults.css';

// Card animation variants (static, no need to recreate)
const CARD_VARIANTS = {
    enter: (dir: 'left' | 'right' | null) => ({
        x: dir === 'left' ? 300 : dir === 'right' ? -300 : 0,
        opacity: 0,
        scale: 0.95,
    }),
    center: {
        x: 0,
        opacity: 1,
        scale: 1,
        transition: { duration: 0.3, ease: 'easeOut' },
    },
    exit: (dir: 'left' | 'right' | null) => ({
        x: dir === 'left' ? -300 : 300,
        opacity: 0,
        scale: 0.95,
        transition: { duration: 0.2 },
    }),
};

interface SwipeableResultsProps {
    venues: VenueWithMatch[];
    onClose: () => void;
    onBack?: () => void;
    onStartOver: () => void;
    currency: 'ZAR' | 'EUR' | 'USD' | 'GBP';
    exchangeRates: Record<string, number>;
}

export const SwipeableResults: React.FC<SwipeableResultsProps> = ({
    venues,
    onClose: _onClose, // Deprecated, keeping for safety but not using in UI
    onBack,
    onStartOver,
    currency = 'ZAR',
    exchangeRates = { ZAR: 1 }
}) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [direction, setDirection] = useState<'left' | 'right' | null>(null);
    const [voteState, setVoteState] = useState<'idle' | 'liked' | 'disliked'>('idle'); // Animation state
    const [imageLoaded, setImageLoaded] = useState(false);
    const [showSwipeGuide, setShowSwipeGuide] = useState(true);
    const [dragOffset, setDragOffset] = useState(0);
    const [isMobile, setIsMobile] = useState(false);
    const [tutorialTouchStart, setTutorialTouchStart] = useState<{ x: number; y: number } | null>(null);

    React.useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 768);
        };
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    // Memoized values
    const currentVenue = useMemo(() => venues[currentIndex], [venues, currentIndex]);
    const hasNext = currentIndex < venues.length - 1;
    const hasPrev = currentIndex > 0;
    const imageUrl = useMemo(() => currentVenue ? getVenueImage(currentVenue) : '', [currentVenue]);

    // Preload next image to keep swipe smooth
    React.useEffect(() => {
        if (currentIndex < venues.length - 1) {
            const nextVenue = venues[currentIndex + 1];
            if (nextVenue) {
                const img = new Image();
                img.src = getVenueImage(nextVenue);
            }
        }
        // Also keep previous image warm if going back
        if (currentIndex > 0) {
            const prevVenue = venues[currentIndex - 1];
            if (prevVenue) {
                const img = new Image();
                img.src = getVenueImage(prevVenue);
            }
        }
    }, [currentIndex, venues]);

    // Format price display with currency conversion
    const priceDisplay = useMemo(() => {
        if (!currentVenue) return '';
        const tier = currentVenue.price_tier?.toLowerCase();

        // Always show "Free" if applicable
        if (tier === 'free' || currentVenue.price_tier === 'Free') return 'Free';
        if (currentVenue.numerical_price === 'Free') return 'Free';

        // Show numerical price if available, converted
        if (currentVenue.numerical_price) {
            return convertPriceString(currentVenue.numerical_price, currency, exchangeRates);
        }

        return currentVenue.price_tier;
    }, [currentVenue, currency, exchangeRates]);

    // Determine which description to show
    const displayDescription = useMemo(() => {
        if (!currentVenue) return '';

        const desc = currentVenue.description;
        const vibe = currentVenue.vibeDescription;

        // If we have no description, fallback to vibe
        if (!desc) return vibe || '';

        // Check for generic Google Places description: "Type (X.X stars, N reviews)"
        // Example: "wine farms (4.8 stars, 453 reviews)"
        const isGeneric = /\(\d+(\.\d+)? stars, \d+ reviews\)$/.test(desc);

        // If description is generic and we have a vibe description, prefer vibe
        if (isGeneric && vibe) {
            return vibe;
        }

        // Otherwise stick with the factual description (or if vibe is missing)
        return desc;
    }, [currentVenue]);
    // Hide swipe guide after first swipe or any interaction
    const dismissGuide = useCallback(() => {
        setShowSwipeGuide(false);
        setTutorialTouchStart(null);
    }, []);

    // Touch handlers for the tutorial overlay - dismiss on any swipe movement
    const handleTutorialTouchStart = useCallback((e: React.TouchEvent) => {
        const touch = e.touches[0];
        setTutorialTouchStart({ x: touch.clientX, y: touch.clientY });
    }, []);

    const handleTutorialTouchMove = useCallback((e: React.TouchEvent) => {
        if (!tutorialTouchStart) return;
        const touch = e.touches[0];
        const deltaX = Math.abs(touch.clientX - tutorialTouchStart.x);
        const deltaY = Math.abs(touch.clientY - tutorialTouchStart.y);
        // Dismiss if user moves finger more than 20px in any direction
        if (deltaX > 20 || deltaY > 20) {
            dismissGuide();
        }
    }, [tutorialTouchStart, dismissGuide]);

    const handleTutorialTouchEnd = useCallback(() => {
        // Still dismiss on tap (touch end without significant movement)
        setTutorialTouchStart(null);
    }, []);

    const goNext = useCallback(() => {
        if (hasNext) {
            setDirection('left');
            setImageLoaded(false);
            dismissGuide();
            setTimeout(() => setCurrentIndex(i => i + 1), 50);
        }
    }, [hasNext, dismissGuide]);

    const goPrev = useCallback(() => {
        if (hasPrev) {
            setDirection('right');
            setImageLoaded(false);
            dismissGuide();
            setTimeout(() => setCurrentIndex(i => i - 1), 50);
        }
    }, [hasPrev, dismissGuide]);

    const handleDrag = useCallback((_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
        setDragOffset(info.offset.x);
    }, []);

    const handleDragEnd = useCallback((_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
        setDragOffset(0);
        const threshold = 60;
        const velocityThreshold = 500;
        const shouldSwipeLeft = (info.velocity.x < -velocityThreshold || info.offset.x < -threshold) && hasNext;
        const shouldSwipeRight = (info.velocity.x > velocityThreshold || info.offset.x > threshold) && hasPrev;

        if (shouldSwipeLeft) {
            goNext();
        } else if (shouldSwipeRight) {
            goPrev();
        }
    }, [hasNext, hasPrev, goNext, goPrev]);

    // Reset vote state when moving to a new card
    React.useEffect(() => {
        setVoteState('idle');
        setDirection(null);
    }, [currentIndex]);

    const handleVote = useCallback((sentiment: 'positive' | 'negative') => {
        if (!currentVenue || voteState !== 'idle') return; // Prevent double taps

        // 1. Trigger Animation State
        setVoteState(sentiment === 'positive' ? 'liked' : 'disliked');

        // 2. Track the vote
        captureFeedback({
            venueId: currentVenue.id,
            venueName: currentVenue.name,
            sentiment,
            actionType: 'vote'
        });

        // 3. Handle Navigation Logic
        if (sentiment === 'negative') {
            // For Dislike: Auto-advance after animation so user doesn't dwell on it
            setTimeout(() => {
                setDirection('left');
                setCurrentIndex(i => i + 1);
            }, 600);
        }
        // For Positive: Do NOT auto-advance. 
        // User wants the card to remain (to Map it), but controls to disappear (handled by voteState).

    }, [currentVenue, voteState]);

    const openInMaps = useCallback(() => {
        if (!currentVenue) return;

        // Track conversion
        captureFeedback({
            venueId: currentVenue.id,
            venueName: currentVenue.name,
            sentiment: 'positive',
            actionType: 'map_click'
        });

        if (currentVenue.maps_url) {
            window.open(currentVenue.maps_url, '_blank', 'noopener,noreferrer');
        } else {
            const query = encodeURIComponent(`${currentVenue.name} Cape Town`);
            window.open(`https://www.google.com/maps/search/?api=1&query=${query}`, '_blank', 'noopener,noreferrer');
        }
    }, [currentVenue]);

    if (!currentVenue) {
        return (
            <div className="results-empty" role="alert">
                <div className="results-empty-icon" aria-hidden="true">🏔️</div>
                <h2>No matches found</h2>
                <p>Try adjusting your preferences</p>
                <button onClick={onBack} className="btn-primary">
                    Adjust Preferences
                </button>
            </div>
        );
    }

    return (
        <div className="results-container">
            {/* Header */}
            <header className="results-header">
                <button onClick={onBack} className="results-close text-btn" aria-label="Back">
                    Back
                </button>
                <span className="results-counter">
                    {currentIndex + 1} / {venues.length}
                </span>
                <button onClick={onStartOver} className="results-restart text-btn" aria-label="Start over">
                    Restart
                </button>
            </header>

            {/* Swipeable Card */}
            <div className="results-card-wrapper">
                <AnimatePresence mode="wait" custom={direction}>
                    <motion.div
                        key={currentVenue.id}
                        className="results-card"
                        custom={direction}
                        variants={CARD_VARIANTS}
                        initial="enter"
                        animate="center"
                        exit="exit"
                        drag="x"
                        dragConstraints={{ left: 0, right: 0 }}
                        dragElastic={0.85}
                        onDrag={handleDrag}
                        onDragEnd={handleDragEnd}
                        whileDrag={{
                            scale: 1.02,
                        }}
                        style={{
                            backgroundImage: `url(${imageUrl})`,
                            rotate: dragOffset / 25, // Subtle rotation: max ~±10 degrees
                        }}
                    >
                        {/* Loading state */}
                        {!imageLoaded && <div className="results-card-skeleton" />}

                        {/* Hidden image to trigger load */}
                        <img
                            src={imageUrl}
                            alt=""
                            // crossOrigin="anonymous" // Removed for local images
                            style={{ display: 'none' }}
                            onLoad={() => setImageLoaded(true)}
                        />


                        {/* Gradient overlay */}
                        <div className="results-card-overlay" />

                        {/* Match badge */}
                        {currentVenue.matchPercentage > 0 && (
                            <div className="results-match-badge-container" style={{ position: 'absolute', top: '12px', right: '12px', zIndex: 10 }}>
                                <div className="results-match-badge" style={{ whiteSpace: 'nowrap', display: 'flex', alignItems: 'center', gap: '4px' }}>
                                    <Sparkles size={14} fill="currentColor" strokeWidth={0} style={{ opacity: 0.8 }} />
                                    {currentVenue.matchPercentage}% match
                                </div>
                            </div>
                        )}

                        {/* Content */}
                        <div className="results-card-content">
                            <h2 className="results-venue-name">{currentVenue.name}</h2>

                            <div className="results-venue-meta">
                                <span className="results-category">{currentVenue.category}</span>
                                {currentVenue.rating && (
                                    <>
                                        <span className="results-divider">•</span>
                                        <span className="results-rating" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                                            <Star size={14} fill="currentColor" strokeWidth={0} />
                                            {currentVenue.rating.toFixed(1)}/5
                                        </span>
                                    </>
                                )}
                                {priceDisplay && (
                                    <>
                                        <span className="results-divider">•</span>
                                        <span className="results-price">{priceDisplay}</span>
                                    </>
                                )}
                                {currentVenue.suburb && (
                                    <>
                                        <span className="results-divider">•</span>
                                        <span className="results-suburb-text">
                                            {currentVenue.suburb}
                                        </span>
                                    </>
                                )}
                            </div>


                            <p className="results-description">
                                {displayDescription}
                            </p>

                            {/* Footer Actions */}
                            <div className="results-card-footer" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: 'auto' }}>
                                {/* Primary Action: Map */}
                                <button onClick={openInMaps} className="results-maps-btn" style={{ flex: 1, justifyContent: 'center', maxWidth: '60%' }}>
                                    <MapPin size={18} />
                                    Open in Maps
                                </button>

                                {/* Secondary Actions: Feedback */}
                                <div className="results-feedback-actions" style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>

                                    <AnimatePresence mode="wait">
                                        {/* Dislike Button */}
                                        {voteState !== 'liked' && (
                                            <motion.button
                                                key="dislike"
                                                onClick={(e) => { e.stopPropagation(); handleVote('negative'); }}
                                                className="feedback-btn dislike"
                                                aria-label="Dislike"
                                                // Animation: Scale Up + Color -> THEN Fade Out/Shrink
                                                animate={{
                                                    scale: voteState === 'disliked' ? [1, 1.1, 0] : 1,
                                                    opacity: voteState === 'disliked' ? 0 : 1,
                                                    backgroundColor: voteState === 'disliked' ? 'hsl(350, 80%, 60%)' : 'rgba(0,0,0,0.4)'
                                                }}
                                                transition={{
                                                    duration: 0.4,
                                                    times: [0, 0.2, 1] // Scale up quickly, then shrink/fade
                                                }}
                                                exit={{ scale: 0, opacity: 0 }}
                                                whileTap={{ scale: 0.9 }}
                                                style={{
                                                    width: '52px', height: '52px', borderRadius: '50%',
                                                    border: '1px solid rgba(255,255,255,0.15)',
                                                    color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    cursor: 'pointer',
                                                    background: 'rgba(0,0,0,0.4)', backdropFilter: 'blur(8px)',
                                                }}
                                            >
                                                <ThumbsDown size={24} />
                                            </motion.button>
                                        )}
                                    </AnimatePresence>

                                    <AnimatePresence mode="wait">
                                        {/* Like Button */}
                                        {voteState !== 'disliked' && (
                                            <motion.button
                                                key="like"
                                                onClick={(e) => { e.stopPropagation(); handleVote('positive'); }}
                                                className="feedback-btn like"
                                                aria-label="Like"
                                                animate={{
                                                    scale: voteState === 'liked' ? [1, 1.1, 0] : 1,
                                                    opacity: voteState === 'liked' ? 0 : 1,
                                                    backgroundColor: voteState === 'liked' ? 'hsl(174, 72%, 40%)' : 'rgba(255,255,255,0.2)'
                                                }}
                                                transition={{
                                                    duration: 0.4,
                                                    times: [0, 0.2, 1]
                                                }}
                                                exit={{ scale: 0, opacity: 0 }}
                                                whileTap={{ scale: 0.9 }}
                                                style={{
                                                    width: '52px', height: '52px', borderRadius: '50%',
                                                    border: '1px solid rgba(255,255,255,0.3)',
                                                    color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
                                                    cursor: 'pointer',
                                                    background: 'hsl(174, 72%, 40%, 0.4)', backdropFilter: 'blur(8px)',
                                                }}
                                            >
                                                <ThumbsUp size={24} />
                                            </motion.button>
                                        )}
                                    </AnimatePresence>
                                </div>

                            </div>
                        </div>
                    </motion.div>
                </AnimatePresence>
            </div>

            {/* Navigation arrows - visible on larger screens */}
            {!isMobile && (
                <div className="results-nav">
                    <button
                        onClick={goPrev}
                        disabled={!hasPrev}
                        className="results-nav-btn"
                        aria-label="Previous venue"
                    >
                        <ChevronLeft size={32} />
                    </button>
                    <button
                        onClick={goNext}
                        disabled={!hasNext}
                        className="results-nav-btn"
                        aria-label="Next venue"
                    >
                        <ChevronRight size={32} />
                    </button>
                </div>
            )}

            {/* Swipe tutorial - mobile only, first card */}
            {isMobile && showSwipeGuide && currentIndex === 0 && (
                <div
                    className="results-swipe-tutorial"
                    onClick={dismissGuide}
                    onTouchStart={handleTutorialTouchStart}
                    onTouchMove={handleTutorialTouchMove}
                    onTouchEnd={handleTutorialTouchEnd}
                >
                    <div className="swipe-tutorial-content">
                        <div className="swipe-hand">👆</div>
                        <p className="swipe-instruction">Swipe left or right to explore</p>
                        <span className="swipe-dismiss">Swipe or tap anywhere to start</span>
                    </div>
                </div>
            )}
        </div>
    );
};
