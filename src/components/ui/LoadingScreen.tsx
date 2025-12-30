import React, { useEffect, useState, useRef, useMemo } from 'react';
import './LoadingScreen.css';
import { getLoadingWords } from '../../data/loadingWords';
import { VenueWithMatch } from '../../utils/matcher';

interface LoadingScreenProps {
    isVisible: boolean;
    touristLevel: number | null;
    intent: string | null;
    venues?: VenueWithMatch[];
    onComplete: () => void;
}

// Preload venue images
function preloadImages(venues: VenueWithMatch[]): Promise<void[]> {
    const imageUrls = venues.slice(0, 5).map(v => v.image_url).filter(Boolean);

    return Promise.all(
        imageUrls.map(url =>
            new Promise<void>((resolve) => {
                const img = new Image();
                img.onload = () => resolve();
                img.onerror = () => resolve(); // Don't block on errors
                img.src = url as string;
            })
        )
    );
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({
    isVisible,
    touristLevel,
    intent,
    venues = [],
    onComplete
}) => {
    const [isDone, setIsDone] = useState(false);
    const [imagesReady, setImagesReady] = useState(false);
    const minDuration = useRef(4000); // Minimum 4s for animation
    const startTime = useRef<number>(0);

    // Select curated words based on tourist level & intent
    const sessionWords = useMemo(() => {
        return getLoadingWords(touristLevel, intent);
    }, [isVisible, touristLevel, intent]);

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

            if (document.body) {
                document.body.style.overflow = 'hidden';
            }

            // Wait for minimum duration
            const minTimer = setTimeout(() => {
                // Check if images are ready or wait a bit more
                const checkAndComplete = () => {
                    const elapsed = Date.now() - startTime.current;

                    if (imagesReady || elapsed > 8000) {
                        // Images ready or max time reached
                        setIsDone(true);
                        setTimeout(() => {
                            if (document.body) {
                                document.body.style.overflow = '';
                            }
                            onComplete();
                        }, 1000); // Wait a second on "lekker!"
                    } else {
                        // Images not ready, check again in 500ms
                        setTimeout(checkAndComplete, 500);
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
        } else {
            setIsDone(false);
            setImagesReady(false);
        }
    }, [isVisible, imagesReady, onComplete]);

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
                            {sessionWords.map((word, i) => (
                                <span key={i} className="word">{word}</span>
                            ))}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

