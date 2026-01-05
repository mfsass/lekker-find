
import posthog from 'posthog-js';

// Configuration
export const POSTHOG_KEY = 'phc_toqgOCc0fRah9TJWmdhS8xzctTndxSgMqSU1LCJvr4h';
export const POSTHOG_HOST = 'https://eu.i.posthog.com';

// Data Packet Schema
interface RecommendationContext {
    intent: string;
    moods: string[];
    budget: string;
    touristLevel: number;
}

interface VenueInteraction {
    venueId: string;
    venueName: string;
    sentiment: 'positive' | 'negative';
    actionType: 'vote' | 'map_click';
}

/**
 * Initialize PostHog (called via Provider in main.tsx, but useful for static access)
 */
export const initAnalytics = () => {
    posthog.init(POSTHOG_KEY, {
        api_host: POSTHOG_HOST,
        person_profiles: 'identified_only', // Optimized for anonymous usage
        session_recording: {
            maskAllInputs: false,

        },
        loaded: (_posthog) => {
            // any post-load logic
        }
    });
};

/**
 * Register the "Data Packet" (Super Properties)
 * Call this when the user finishes the questionnaire
 */
export const setRecommendationContext = (context: RecommendationContext) => {
    if (!context) return;

    // Register these properties so they are attached to every subsequent event
    posthog.register({
        context_intent: context.intent,
        context_moods: context.moods,
        context_budget: context.budget,
        context_tourist_level: context.touristLevel,
    });
};

/**
 * Reset context when starting over
 */
export const clearRecommendationContext = () => {
    posthog.unregister('context_intent');
    posthog.unregister('context_moods');
    posthog.unregister('context_budget');
    posthog.unregister('context_tourist_level');
};

/**
 * Capture a specific venue interaction
 */
export const captureFeedback = (interaction: VenueInteraction) => {
    posthog.capture('venue_evaluated', {
        venue_id: interaction.venueId,
        venue_name: interaction.venueName,
        sentiment: interaction.sentiment,
        action_type: interaction.actionType,
        // Note: detailed context is already attached via register()
    });
};
