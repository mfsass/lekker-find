import React, { useEffect, useState, useRef, useMemo } from 'react';
import './LoadingScreen.css';
import { getLoadingWords } from '../../data/loadingWords';
import { VenueWithMatch } from '../../utils/matcher';

import { getVenueImage } from '../../utils/imageHelper';

interface LoadingScreenProps {
    isVisible: boolean;
    touristLevel: number | null;
    intent: string | null;
    venues?: VenueWithMatch[];
    onComplete: () => void;
}

// Preload venue images
function preloadImages(venues: VenueWithMatch[]): Promise<void[]> {
    // Preload more images (up to 15) to make the swipe experience smooth
    // We prioritize the first few images to ensure immediate availability
    const targetVenues = venues.slice(0, 15);
    const imageUrls = targetVenues.map(getVenueImage).filter(Boolean);

    // Dedup URLs
    const uniqueUrls = [...new Set(imageUrls)];

    return Promise.all(
        uniqueUrls.map(url =>
            new Promise<void>((resolve) => {
                const img = new Image();
                // We use crossOrigin to help with CORS but let referrer pass through 
                // for Google Maps API key verification
                // Local images don't need crossOrigin usually, but safe to omit if local
                // img.crossOrigin = 'anonymous'; 
                img.onload = () => resolve();
                img.onerror = () => {
                    const cleanUrl = typeof url === 'string' ? url.split('?')[0] : 'Unknown URL';
                    console.warn(`Failed to preload image: ${cleanUrl}`);
                    resolve(); // Resolve anyway to not block
                };
                img.src = url as string;
            })
        )
    );
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
    isVisible,
    venues = [],
    onComplete
}) => {
    const [isDone, setIsDone] = useState(false);
    const [imagesReady, setImagesReady] = useState(false);
    const minDuration = useRef(3000); // Minimum 3s for animation
    const startTime = useRef<number>(0);

    // Select curated words
    // We stabilize this so it doesn't change during the visible phase
    const sessionWords = useMemo(() => {
        if (!isVisible) return [];
        return getLoadingWords();
    }, [isVisible]); // Only regenerate when isVisible flips from false to true

    // Preload images
    useEffect(() => {
        if (isVisible && venues.length > 0) {
            setImagesReady(false);
            preloadImages(venues).then(() => {
                setImagesReady(true);
            });
        }
    }, [isVisible, venues]);

    useEffect(() => {
        if (isVisible) {
            startTime.current = Date.now();
            setIsDone(false); // Reset done state

            if (document.body) {
                document.body.style.overflow = 'hidden';
            }

            // Wait for minimum duration (3s)
            const minTimer = setTimeout(() => {
                const checkAndComplete = () => {
                    const elapsed = Date.now() - startTime.current;

                    // Images ready OR hit the 8s snappy cap
                    if (imagesReady || elapsed > 8000) {
                        setIsDone(true);
                        setTimeout(() => {
                            if (document.body) {
                                document.body.style.overflow = '';
                            }
                            onComplete();
                        }, 800); // Shorter beat on "lekker!" to stay snappy
                    } else {
                        // Keep checking every 200ms for faster feedback
                        setTimeout(checkAndComplete, 200);
                    }
                };

                checkAndComplete();
            }, minDuration.current);

            return () => {
                clearTimeout(minTimer);
                if (document.body) {
                    document.body.style.overflow = '';
                }
            };
        }
    }, [isVisible, imagesReady, onComplete]); // Simplified dependencies for better stability

    if (!isVisible) return null;

    return (
        <div className="loading-screen-container">
            <div className="loader-card">
                {isDone ? (
                    <div className="loader" style={{ justifyContent: 'center' }}>
                        <span className="completion-message">lekker!</span>
                    </div>
                ) : (
                    <div className="loader">
                        <p>Loading</p>

                        <div className="words">
                            {[...sessionWords, sessionWords[0]].map((word, i) => (
                                <span key={i} className="word">{word}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

