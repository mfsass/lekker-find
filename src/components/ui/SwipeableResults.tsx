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
import { MapPin, ChevronLeft, ChevronRight, X, RotateCcw, Star } from 'lucide-react';
import { VenueWithMatch } from '../../utils/matcher';
import { convertPriceString } from '../../utils/currency';
import './SwipeableResults.css';

// Fallback images by category (Unsplash URLs)
const FALLBACK_IMAGES: Record<string, string> = {
    food: 'https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1200&q=80',
    drink: 'https://images.unsplash.com/photo-1514362545857-3bc16549766b?auto=format&fit=crop&w=1200&q=80',
    nature: 'https://images.unsplash.com/photo-1580060839134-75a5edca2e99?auto=format&fit=crop&w=1200&q=80',
    activity: 'https://images.unsplash.com/photo-1502680390469-be75c86b636f?auto=format&fit=crop&w=1200&q=80',
    culture: 'https://images.unsplash.com/photo-1576485290814-1c72aa4bbb8e?auto=format&fit=crop&w=1200&q=80',
};

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

function getVenueImage(venue: VenueWithMatch): string {
    // Priority: 1. External image_url, 2. Local venue image, 3. Category fallback
    if (venue.image_url) return venue.image_url;

    // Use local image based on venue id (e.g., v0.jpg, v1.jpg)
    // The id format is "v{idx}" so we extract the number
    const idMatch = venue.id?.match(/v(\d+)/);
    if (idMatch) {
        return `/images/venues/v${idMatch[1]}.jpg`;
    }

    const category = venue.category?.toLowerCase() || 'nature';
    return FALLBACK_IMAGES[category] || FALLBACK_IMAGES.nature;
}

interface SwipeableResultsProps {
    venues: VenueWithMatch[];
    onClose: () => void;
    onStartOver: () => void;
    currency: 'ZAR' | 'EUR' | 'USD' | 'GBP';
    exchangeRates: Record<string, number>;
}

export const SwipeableResults: React.FC<SwipeableResultsProps> = ({
    venues,
    onClose,
    onStartOver,
    currency = 'ZAR',
    exchangeRates = { ZAR: 1 }
}) => {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [direction, setDirection] = useState<'left' | 'right' | null>(null);
    const [imageLoaded, setImageLoaded] = useState(false);
    const [showSwipeGuide, setShowSwipeGuide] = useState(true);

    // Detect if mobile (use screen width - more reliable than touch detection)
    // Touchscreen laptops should still show arrows
    const [isMobile, setIsMobile] = useState(false);

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

        // If only tier is available (R, RR, RRR), maybe imply range?
        // For now just return tier if no numerical price
        return currentVenue.price_tier;
    }, [currentVenue, currency, exchangeRates]);

    // Hide swipe guide after first swipe
    const dismissGuide = useCallback(() => {
        setShowSwipeGuide(false);
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

    const handleDragEnd = useCallback((_event: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
        const threshold = 100;
        if (info.offset.x < -threshold && hasNext) {
            goNext();
        } else if (info.offset.x > threshold && hasPrev) {
            goPrev();
        }
    }, [hasNext, hasPrev, goNext, goPrev]);

    const openInMaps = useCallback(() => {
        if (currentVenue?.maps_url) {
            window.open(currentVenue.maps_url, '_blank', 'noopener,noreferrer');
        } else if (currentVenue) {
            // Fallback: Google search
            const query = encodeURIComponent(`${currentVenue.name} Cape Town`);
            window.open(`https://www.google.com/maps/search/?api=1&query=${query}`, '_blank', 'noopener,noreferrer');
        }
    }, [currentVenue]);

    // Empty state
    if (!currentVenue) {
        return (
            <div className="results-empty" role="alert">
                <div className="results-empty-icon" aria-hidden="true">🏔️</div>
                <h2>No matches found</h2>
                <p>Try adjusting your preferences</p>
                <button onClick={onStartOver} className="btn-primary">
                    Start Over
                </button>
            </div>
        );
    }

    return (
        <div className="results-container">
            {/* Header */}
            <header className="results-header">
                <button onClick={onClose} className="results-close" aria-label="Close">
                    <X size={24} />
                </button>
                <span className="results-counter">
                    {currentIndex + 1} / {venues.length}
                </span>
                <button onClick={onStartOver} className="results-restart" aria-label="Start over">
                    <RotateCcw size={20} />
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
                        dragElastic={0.7}
                        onDragEnd={handleDragEnd}
                        style={{
                            backgroundImage: `url(${imageUrl})`,
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
                            <div className="results-match-badge">
                                {currentVenue.matchPercentage}% match
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
                            </div>

                            <p className="results-description">
                                {currentVenue.description}
                            </p>

                            {/* Open in Maps */}
                            <button onClick={openInMaps} className="results-maps-btn">
                                <MapPin size={18} />
                                Open in Maps
                            </button>
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
                <div className="results-swipe-tutorial" onClick={dismissGuide}>
                    <div className="swipe-tutorial-content">
                        <div className="swipe-hand">👆</div>
                        <p className="swipe-instruction">Swipe left or right to explore</p>
                        <span className="swipe-dismiss">Tap to dismiss</span>
                    </div>
                </div>
            )}
        </div>
    );
};
