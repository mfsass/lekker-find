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
import { motion, AnimatePresence, PanInfo, TargetAndTransition, VariantLabels } from 'framer-motion';
import { MapPin, ChevronLeft, ChevronRight, Star, Sparkles, Search, SearchX, Hand, AlertTriangle, ShieldAlert, X } from 'lucide-react';
import { VenueWithMatch } from '../../utils/matcher';
import { convertPriceString } from '../../utils/currency';
import { getVenueFallbackImage, getVenueImage } from '../../utils/imageHelper';
import { captureFeedback } from '../../utils/analytics';
import { ShareButton } from './ShareButton';
import { ShareState } from '../../utils/shareState';
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

// Isolated Card Component to handle its own state (image loading, votes)
// This prevents state leakage and race conditions during transitions
const ResultsCard = React.memo(({
    venue,
    direction,
    dragHandlers,
    openInMaps,
    onTap,
    currency,
    exchangeRates,
    selectedVibes,
    shareState,
    onSafetyClick
}: {
    venue: VenueWithMatch;
    direction: 'left' | 'right' | null;
    dragHandlers: {
        drag: "x";
        dragConstraints: { left: number; right: number };
        dragElastic: number;
        onDragStart?: (e: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => void;
        onDrag: (e: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => void;
        onDragEnd: (e: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => void;
        whileDrag: TargetAndTransition | VariantLabels;
    };
    // onVote removed
    openInMaps: (venue: VenueWithMatch, e?: React.MouseEvent | React.TouchEvent) => void;
    onTap: (e: MouseEvent | TouchEvent | PointerEvent) => void;
    currency: 'ZAR' | 'EUR' | 'USD' | 'GBP';
    exchangeRates: Record<string, number>;
    selectedVibes?: string[];
    shareState?: ShareState;
    onSafetyClick: (e: React.MouseEvent | React.TouchEvent) => void;
}) => {
    const imageUrl = useMemo(() => getVenueImage(venue), [venue]);
    const fallbackImageUrl = useMemo(() => getVenueFallbackImage(venue), [venue]);
    const [resolvedImageUrl, setResolvedImageUrl] = useState(imageUrl);
    const [imageLoaded, setImageLoaded] = useState(false);
    const [fallbackAttempted, setFallbackAttempted] = useState(false);
    const [imageFailed, setImageFailed] = useState(false);
    // localVoteState removed
    const imgRef = React.useRef<HTMLImageElement>(null);

    React.useEffect(() => {
        setResolvedImageUrl(imageUrl);
        setImageLoaded(false);
        setFallbackAttempted(false);
        setImageFailed(false);
    }, [imageUrl, venue]);

    // Check if image is already cached/loaded on mount
    React.useEffect(() => {
        if (imgRef.current && imgRef.current.complete && imgRef.current.naturalWidth > 0) {
            setImageLoaded(true);
        }
    }, [resolvedImageUrl]);

    const handleImageLoad = useCallback(() => {
        setImageLoaded(true);
        setImageFailed(false);
    }, []);

    const handleImageError = useCallback(() => {
        const canFallback = !!fallbackImageUrl && resolvedImageUrl !== fallbackImageUrl;
        if (!fallbackAttempted && canFallback) {
            setFallbackAttempted(true);
            setImageLoaded(false);
            setResolvedImageUrl(fallbackImageUrl);
            return;
        }
        setImageLoaded(true);
        setImageFailed(true);
    }, [fallbackAttempted, fallbackImageUrl, resolvedImageUrl]);

    // Handle local vote interaction removed

    // Format price
    const priceDisplay = useMemo(() => {
        const tier = venue.price_tier?.toLowerCase();
        if (tier === 'free' || venue.price_tier === 'Free') return 'Free';
        if (venue.numerical_price === 'Free') return 'Free';
        if (venue.numerical_price) {
            return convertPriceString(venue.numerical_price, currency, exchangeRates);
        }
        return venue.price_tier;
    }, [venue, currency, exchangeRates]);

    // Determine description
    const displayDescription = useMemo(() => {
        const desc = venue.description;
        const vibe = venue.vibeDescription;
        if (!desc) return vibe || '';
        // Check for generic Google Places description like "wine farms (4.8 stars, 453 reviews)"
        const isGeneric = /\(\d+(\.\d+)? stars, \d+ reviews\)$/.test(desc);
        if (isGeneric && vibe) return vibe;
        return desc;
    }, [venue]);

    return (
        <motion.div
            className="results-card"
            custom={direction}
            variants={CARD_VARIANTS}
            initial="enter"
            animate="center"
            exit="exit"
            {...dragHandlers}
            onTap={onTap}
            style={{
                backgroundImage: `url(${resolvedImageUrl})`,
                // We can't access dragOffset easily here without context or prop, 
                // but simpler is better for stability. Removing rotation for now to simplify prop drilling.
            }}
        >
            {/* Loading state - managed locally per card instance */}
            {!imageLoaded && <div className="results-card-skeleton" />}
            {imageFailed && <div className="results-card-fallback" />}

            {/* Hidden image to trigger load */}
            <img
                ref={imgRef}
                src={resolvedImageUrl}
                alt=""
                style={{ display: 'none' }}
                onLoad={handleImageLoad}
                onError={handleImageError}
            />

            {/* Gradient overlay for text readability */}
            <div
                className="results-card-overlay"
                aria-hidden="true"
            />

            {/* Match badge with vibes tooltip (hover on desktop, tap on mobile) */}
            {venue.matchPercentage > 0 && (
                <div className="results-match-badge-container" style={{
                    position: 'absolute',
                    top: '12px',
                    right: '12px',
                    zIndex: 10,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'flex-end',
                    gap: '12px'
                }}>
                    <motion.div
                        className="results-match-badge"
                        style={{
                            position: 'relative', // Override absolute from CSS
                            top: 'auto',
                            right: 'auto',
                            whiteSpace: 'nowrap',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '4px',
                            cursor: 'pointer'
                        }}
                        title={selectedVibes && selectedVibes.length > 0
                            ? `Your vibes: ${selectedVibes.join(', ')}`
                            : 'Matched based on your preferences'}
                        onClick={(e) => {
                            e.stopPropagation();
                            if (selectedVibes && selectedVibes.length > 0) {
                                alert(`Your vibes: ${selectedVibes.join(', ')}`);
                            }
                        }}
                        onPointerDown={(e) => e.stopPropagation()}
                        onTap={(e) => e.stopPropagation()}
                        role="button"
                        aria-label={`${venue.matchPercentage}% match - tap to see your selected vibes`}
                    >
                        <Sparkles size={14} fill="currentColor" strokeWidth={0} style={{ opacity: 0.8 }} />
                        {venue.matchPercentage}% match
                    </motion.div>
                </div>
            )}

            {/* Content */}
            <div className="results-card-content">
                {venue.safety_level && venue.safety_level !== 'normal' && (
                    <motion.button
                        className={`safety-pill ${venue.safety_level}`}
                        onClick={(e) => {
                            e.stopPropagation();
                            onSafetyClick(e);
                        }}
                        onPointerDown={(e) => e.stopPropagation()}
                        onTap={(e) => e.stopPropagation()}
                        title="Click for safety info"
                    >
                        <span className="safety-pill-dot" />
                        {venue.safety_level === 'high' ? 'Local Area' : 'Caution Area'}
                    </motion.button>
                )}
                <h2 className="results-venue-name">{venue.name}</h2>

                <div className="results-venue-meta">
                    <span className="results-category">{venue.category}</span>
                    {venue.rating && (
                        <>
                            <span className="results-divider">•</span>
                            <span className="results-rating" style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                                <Star size={14} fill="currentColor" strokeWidth={0} />
                                {venue.rating.toFixed(1)}/5
                            </span>
                        </>
                    )}
                    {priceDisplay && (
                        <>
                            <span className="results-divider">•</span>
                            <span className="results-price">{priceDisplay}</span>
                        </>
                    )}
                    {venue.suburb && (
                        <>
                            <span className="results-divider">•</span>
                            <span className="results-suburb-text" style={{ display: 'inline-flex', alignItems: 'center', gap: '3px' }}>
                                <MapPin size={12} style={{ opacity: 0.8 }} />
                                {venue.suburb}
                            </span>
                        </>
                    )}
                </div>

                <p className="results-description">
                    {displayDescription}
                </p>

                {/* Footer Actions */}
                <div className="results-card-footer">
                    <motion.button
                        onClick={(e) => {
                            e.stopPropagation();
                            openInMaps(venue, e);
                        }}
                        onPointerDown={(e) => e.stopPropagation()}
                        onTap={(e) => e.stopPropagation()}
                        className="results-maps-btn"
                        style={{ flex: 1, justifyContent: 'center' }}
                        aria-label="Open location in Maps"
                        data-clarity-action="map-click"
                    >
                        <MapPin size={20} />
                        Maps
                    </motion.button>

                    {shareState && (
                        <motion.div
                            onClick={(e) => e.stopPropagation()}
                            onPointerDown={(e) => e.stopPropagation()}
                            onTap={(e) => e.stopPropagation()}
                            className="results-share-wrapper"
                        >
                            <ShareButton
                                state={shareState}
                                className="results-share-btn"
                            />
                        </motion.div>
                    )}
                </div>
            </div>
        </motion.div>
    );
});

interface SwipeableResultsProps {
    venues: VenueWithMatch[];
    onClose: () => void;
    onBack?: () => void;
    onStartOver: () => void;
    onAdjustVibes?: () => void;
    currency: 'ZAR' | 'EUR' | 'USD' | 'GBP';
    exchangeRates: Record<string, number>;
    isCuriousMode?: boolean;
    selectedVibes?: string[];
    shareState?: ShareState;
    initialIndex?: number;
}

export const SwipeableResults: React.FC<SwipeableResultsProps> = ({
    venues,
    onClose: _onClose,
    onBack,
    onStartOver,
    onAdjustVibes,
    currency = 'ZAR',
    exchangeRates = { ZAR: 1 },
    isCuriousMode = false,
    selectedVibes = [],
    shareState,
    initialIndex = 0
}) => {
    const [currentIndex, setCurrentIndex] = useState(initialIndex);
    const [direction, setDirection] = useState<'left' | 'right' | null>(null);
    // Removed parent-level voteState and imageLoaded state
    const [showSwipeGuide, setShowSwipeGuide] = useState(true);
    // Removed unused dragOffset
    const [isMobile, setIsMobile] = useState(false);
    const [tutorialTouchStart, setTutorialTouchStart] = useState<{ x: number; y: number } | null>(null);
    const [showEndMessage, setShowEndMessage] = useState(false);

    const [showSafetyPopup, setShowSafetyPopup] = useState(false);

    React.useEffect(() => {
        const checkMobile = () => {
            setIsMobile(window.innerWidth < 768);
        };
        checkMobile();
        window.addEventListener('resize', checkMobile);
        return () => window.removeEventListener('resize', checkMobile);
    }, []);

    const currentVenue = useMemo(() => venues[currentIndex], [venues, currentIndex]);
    const hasNext = currentIndex < venues.length - 1;
    const hasPrev = currentIndex > 0;

    // Preload next image logic remains same
    React.useEffect(() => {
        if (currentIndex < venues.length - 1) {
            const nextVenue = venues[currentIndex + 1];
            if (nextVenue) {
                const img = new Image();
                img.src = getVenueImage(nextVenue);
            }
        }
        if (currentIndex > 0) {
            const prevVenue = venues[currentIndex - 1];
            if (prevVenue) {
                const img = new Image();
                img.src = getVenueImage(prevVenue);
            }
        }
    }, [currentIndex, venues]);

    const dismissGuide = useCallback(() => {
        setShowSwipeGuide(false);
        setTutorialTouchStart(null);
    }, []);

    const handleTutorialTouchStart = useCallback((e: React.TouchEvent) => {
        const touch = e.touches[0];
        setTutorialTouchStart({ x: touch.clientX, y: touch.clientY });
    }, []);

    const handleTutorialTouchMove = useCallback((e: React.TouchEvent) => {
        if (!tutorialTouchStart) return;
        const touch = e.touches[0];
        const deltaX = Math.abs(touch.clientX - tutorialTouchStart.x);
        const deltaY = Math.abs(touch.clientY - tutorialTouchStart.y);
        if (deltaX > 20 || deltaY > 20) {
            dismissGuide();
        }
    }, [tutorialTouchStart, dismissGuide]);

    const handleTutorialTouchEnd = useCallback(() => {
        setTutorialTouchStart(null);
    }, []);

    const goNext = useCallback(() => {
        if (hasNext) {
            setDirection('left');
            dismissGuide();
            setCurrentIndex(prev => prev + 1);
            setShowEndMessage(false);
        } else {
            // User tried to go past last card - show end message
            setShowEndMessage(true);
        }
    }, [hasNext, dismissGuide]);

    const goPrev = useCallback(() => {
        if (hasPrev) {
            setDirection('right');
            dismissGuide();
            setCurrentIndex(prev => prev - 1);
            setShowEndMessage(false);
        }
    }, [hasPrev, dismissGuide]);

    const isSwiping = React.useRef(false);

    const handleDragStart = useCallback(() => {
        isSwiping.current = true;
    }, []);

    const handleDrag = useCallback((_event: MouseEvent | TouchEvent | PointerEvent, _info: PanInfo) => {
        // Drag offset tracking removed for now
    }, []);

    const handleDragEnd = useCallback((_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
        const threshold = 60;
        const velocityThreshold = 500;
        const swipedLeft = info.velocity.x < -velocityThreshold || info.offset.x < -threshold;
        const swipedRight = info.velocity.x > velocityThreshold || info.offset.x > threshold;

        if (swipedLeft && hasNext) {
            goNext();
        } else if (swipedRight && hasPrev) {
            goPrev();
        } else if (swipedLeft && !hasNext) {
            // User swiped left on last card - show end message
            setShowEndMessage(true);
        }

        // Reset swiping flag after a short delay to block immediate tap events
        setTimeout(() => {
            isSwiping.current = false;
        }, 50);
    }, [hasNext, hasPrev, goNext, goPrev]);

    const handleCardTap = useCallback((e: MouseEvent | TouchEvent | PointerEvent) => {
        if (isSwiping.current) return;

        // Prevent advancement if tapping an interactive element (buttons, pills, badges)
        // framer-motion's onTap sometimes bypasses stopPropagation, so this is a robust fall-back
        const target = e?.target as HTMLElement;
        if (target && (
            target.closest('button') ||
            target.closest('.results-match-badge') ||
            target.closest('.safety-pill') ||
            target.closest('.share-btn')
        )) {
            return;
        }

        goNext();
    }, [goNext]);

    // handleVote removed

    const openInMaps = useCallback((venue: VenueWithMatch, e?: React.MouseEvent | React.TouchEvent) => {
        if (e) e.stopPropagation();
        captureFeedback({
            venueId: venue.id,
            venueName: venue.name,
            sentiment: 'positive',
            actionType: 'map_click',
            source: isCuriousMode ? 'curious_shuffle' : 'recommendation_engine'
        });

        if (venue.maps_url) {
            window.open(venue.maps_url, '_blank', 'noopener,noreferrer');
        } else {
            const query = encodeURIComponent(`${venue.name} Cape Town`);
            window.open(`https://www.google.com/maps/search/?api=1&query=${query}`, '_blank', 'noopener,noreferrer');
        }
    }, [isCuriousMode]);

    const handleSafetyClick = useCallback((e: React.MouseEvent | React.TouchEvent) => {
        e.stopPropagation();
        setShowSafetyPopup(true);
    }, []);

    const closeSafetyPopup = useCallback(() => {
        setShowSafetyPopup(false);
    }, []);

    if (!currentVenue) {
        return (
            <div className="results-empty" role="alert">
                <div className="results-empty-icon" aria-hidden="true"><SearchX size={48} /></div>
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
            <header className="results-header">
                <button onClick={onBack} className="results-close text-btn" aria-label="Back">
                    Back
                </button>
                <div className="results-header-center">
                    <span className="results-counter">
                        {currentIndex + 1} / {venues.length}
                    </span>
                    {/* Desktop: Show share in header. Mobile: Key share action is on the card */}
                    {/* Share removed from header */}
                </div>
                <button onClick={onStartOver} className="results-restart text-btn" aria-label="Start over">
                    Restart
                </button>
            </header>

            <div className="results-card-wrapper">
                <AnimatePresence initial={false} custom={direction}>
                    <ResultsCard
                        key={currentVenue.id}
                        venue={currentVenue}
                        direction={direction}
                        dragHandlers={{
                            drag: "x",
                            dragConstraints: { left: 0, right: 0 },
                            dragElastic: 0.85,
                            onDragStart: handleDragStart,
                            onDrag: handleDrag,
                            onDragEnd: handleDragEnd,
                            whileDrag: { scale: 1.02 }
                        }}
                        openInMaps={openInMaps}
                        onTap={handleCardTap}
                        currency={currency}
                        exchangeRates={exchangeRates}
                        selectedVibes={selectedVibes}
                        shareState={shareState ? (isCuriousMode ? { venueId: currentVenue.id } : { ...shareState, index: currentIndex }) : undefined}
                        onSafetyClick={handleSafetyClick}
                    />
                </AnimatePresence>

                {/* End of results overlay */}
                <AnimatePresence>
                    {
                        showEndMessage && (
                            <motion.div
                                className="results-end-message"
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                transition={{ duration: 0.3, ease: 'easeOut' }}
                            >
                                <div className="results-end-content">
                                    <div className="results-end-icon" aria-hidden="true">
                                        <Search size={48} />
                                    </div>
                                    <h3 className="results-end-title">Not quite right?</h3>
                                    <p className="results-end-subtitle">Try adjusting your vibes or budget for better matches</p>
                                    <button
                                        className="results-end-restart-btn"
                                        onClick={onAdjustVibes || onStartOver}
                                    >
                                        Try Different Selections
                                    </button>
                                    <button
                                        className="results-end-back-btn"
                                        onClick={() => setShowEndMessage(false)}
                                    >
                                        Cancel
                                    </button>

                                    {!isCuriousMode && shareState && (
                                        <div className="results-end-share">
                                            <p className="results-end-share-text">Share these matches with friends</p>
                                            <ShareButton
                                                state={{ ...shareState, index: 0 }} // Share from start
                                                venueName={venues[0]?.name}
                                                className="share-btn-primary" // New class for primary style
                                            />
                                        </div>
                                    )}
                                </div>
                            </motion.div>
                        )
                    }
                </AnimatePresence >

                {/* Safety Popup */}
                <AnimatePresence>
                    {
                        showSafetyPopup && (
                            <motion.div
                                className="safety-popup-overlay"
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                exit={{ opacity: 0 }}
                                onClick={closeSafetyPopup}
                            >
                                <motion.div
                                    className="safety-popup-card"
                                    initial={{ scale: 0.9, opacity: 0, y: 20 }}
                                    animate={{ scale: 1, opacity: 1, y: 0 }}
                                    exit={{ scale: 0.9, opacity: 0, y: 20 }}
                                    onClick={(e) => e.stopPropagation()}
                                >
                                    <button
                                        className="safety-popup-close"
                                        onClick={closeSafetyPopup}
                                        aria-label="Close"
                                    >
                                        <X size={20} />
                                    </button>

                                    <div className={`safety-popup-icon-wrapper ${currentVenue.safety_level}`}>
                                        {currentVenue.safety_level === 'high' ? (
                                            <ShieldAlert size={48} />
                                        ) : (
                                            <AlertTriangle size={48} />
                                        )}
                                    </div>

                                    <h3 className="safety-popup-title">
                                        {currentVenue.safety_level === 'high' ? 'Local Area Alert' : 'Heads Up!'}
                                    </h3>

                                    <p className="safety-popup-text">
                                        {currentVenue.safety_level === 'high'
                                            ? "This area requires extra caution. We recommend staying aware of your surroundings and using reliable transport."
                                            : "This area is generally fine, just be aware of your surroundings like in any busy city."}
                                    </p>

                                    <p className="safety-popup-subtext">
                                        Visit at your own discretion and have a lekker time!
                                    </p>

                                    <div className="safety-popup-actions">
                                        <button className="safety-popup-btn primary" onClick={closeSafetyPopup}>
                                            Got it
                                        </button>
                                        {hasNext && (
                                            <button
                                                className="safety-popup-btn secondary"
                                                onClick={() => {
                                                    closeSafetyPopup();
                                                    goNext();
                                                }}
                                            >
                                                Next Location
                                            </button>
                                        )}
                                    </div>
                                </motion.div>
                            </motion.div>
                        )
                    }
                </AnimatePresence >
            </div >

            {!isMobile && (
                <div className="results-nav">
                    <button onClick={goPrev} disabled={!hasPrev} className="results-nav-btn" aria-label="Previous venue">
                        <ChevronLeft size={32} />
                    </button>
                    <button onClick={goNext} disabled={!hasNext && showEndMessage} className="results-nav-btn" aria-label="Next venue">
                        <ChevronRight size={32} />
                    </button>
                </div>
            )}

            {
                isMobile && showSwipeGuide && currentIndex === 0 && (
                    <div
                        className="results-swipe-tutorial"
                        onClick={dismissGuide}
                        onTouchStart={handleTutorialTouchStart}
                        onTouchMove={handleTutorialTouchMove}
                        onTouchEnd={handleTutorialTouchEnd}
                    >
                        <div className="swipe-tutorial-content">
                            <div className="swipe-hand">
                                <Hand size={48} />
                            </div>
                            <p className="swipe-instruction">Swipe left or right to explore</p>
                            <span className="swipe-dismiss">Swipe or tap anywhere to start</span>
                        </div>
                    </div>
                )
            }

        </div >
    );
};
