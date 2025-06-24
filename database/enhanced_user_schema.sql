-- Enhanced User Management Schema for Opportunity Dashboard
-- This extends the existing schema with user-specific features

-- User Profiles table (extends Supabase auth.users)
CREATE TABLE user_profiles (
    id UUID REFERENCES auth.users(id) PRIMARY KEY,
    full_name TEXT,
    company TEXT,
    role TEXT,
    bio TEXT,
    avatar_url TEXT,
    phone TEXT,
    website TEXT,
    linkedin_url TEXT,
    
    -- Preferences
    email_notifications BOOLEAN DEFAULT true,
    push_notifications BOOLEAN DEFAULT true,
    weekly_digest BOOLEAN DEFAULT true,
    
    -- Dashboard preferences
    default_view TEXT DEFAULT 'dashboard', -- dashboard, opportunities, search
    items_per_page INTEGER DEFAULT 25,
    preferred_sort TEXT DEFAULT 'relevance_score',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Saved Searches table
CREATE TABLE saved_searches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    
    -- Search parameters
    keywords TEXT,
    min_value DECIMAL(15,2),
    max_value DECIMAL(15,2),
    source_types TEXT[], -- array of source types
    agencies TEXT[], -- array of agency names
    locations TEXT[], -- array of locations
    date_range_start DATE,
    date_range_end DATE,
    
    -- Notification settings for this search
    notify_new_matches BOOLEAN DEFAULT false,
    last_notification_sent TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    match_count INTEGER DEFAULT 0,
    last_run TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User Favorites table
CREATE TABLE user_favorites (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    opportunity_id INTEGER REFERENCES opportunities(id) ON DELETE CASCADE,
    notes TEXT,
    tags TEXT[],
    is_archived BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, opportunity_id)
);

-- User Activity Log table
CREATE TABLE user_activity_log (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    activity_type TEXT NOT NULL, -- 'login', 'search', 'view_opportunity', 'save_favorite', etc.
    activity_data JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enhanced User Preferences table (replace existing)
DROP TABLE IF EXISTS user_preferences;
CREATE TABLE user_preferences (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
    
    -- Search preferences
    keywords JSONB DEFAULT '[]'::jsonb,
    preferred_sources JSONB DEFAULT '[]'::jsonb,
    excluded_agencies JSONB DEFAULT '[]'::jsonb,
    
    -- Scoring preferences
    scoring_weights JSONB DEFAULT '{
        "relevance": 0.3,
        "urgency": 0.25,
        "value": 0.25,
        "competition": 0.2
    }'::jsonb,
    
    -- Notification preferences
    notification_settings JSONB DEFAULT '{
        "email": true,
        "push": true,
        "digest": true,
        "new_matches": false,
        "deadlines": true
    }'::jsonb,
    
    -- Dashboard preferences
    dashboard_settings JSONB DEFAULT '{
        "default_tab": "dashboard",
        "chart_preferences": ["opportunity_types", "agencies", "timeline"],
        "quick_filters": ["high_value", "urgent", "relevant"]
    }'::jsonb,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Opportunity Notes table (user-specific notes on opportunities)
CREATE TABLE opportunity_notes (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    opportunity_id INTEGER REFERENCES opportunities(id) ON DELETE CASCADE,
    note TEXT NOT NULL,
    is_private BOOLEAN DEFAULT true,
    tags TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(user_id, opportunity_id)
);

-- User Teams table (for collaborative features)
CREATE TABLE user_teams (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    is_active BOOLEAN DEFAULT true,
    settings JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Team Members table
CREATE TABLE team_members (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    team_id UUID REFERENCES user_teams(id) ON DELETE CASCADE,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    role TEXT DEFAULT 'member', -- 'owner', 'admin', 'member', 'viewer'
    permissions JSONB DEFAULT '{}'::jsonb,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    UNIQUE(team_id, user_id)
);

-- Indexes for performance
CREATE INDEX idx_user_profiles_user_id ON user_profiles(id);
CREATE INDEX idx_saved_searches_user_id ON saved_searches(user_id);
CREATE INDEX idx_saved_searches_active ON saved_searches(user_id, is_active);
CREATE INDEX idx_user_favorites_user_id ON user_favorites(user_id);
CREATE INDEX idx_user_favorites_opportunity ON user_favorites(opportunity_id);
CREATE INDEX idx_user_activity_log_user_id ON user_activity_log(user_id);
CREATE INDEX idx_user_activity_log_created_at ON user_activity_log(created_at);
CREATE INDEX idx_opportunity_notes_user_id ON opportunity_notes(user_id);
CREATE INDEX idx_opportunity_notes_opportunity_id ON opportunity_notes(opportunity_id);
CREATE INDEX idx_team_members_team_id ON team_members(team_id);
CREATE INDEX idx_team_members_user_id ON team_members(user_id);

-- RLS (Row Level Security) policies
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_favorites ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE opportunity_notes ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_teams ENABLE ROW LEVEL SECURITY;
ALTER TABLE team_members ENABLE ROW LEVEL SECURITY;

-- User can only access their own data
CREATE POLICY "Users can view own profile" ON user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON user_profiles FOR UPDATE USING (auth.uid() = id);
CREATE POLICY "Users can insert own profile" ON user_profiles FOR INSERT WITH CHECK (auth.uid() = id);

CREATE POLICY "Users can manage own searches" ON saved_searches FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own favorites" ON user_favorites FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can view own activity" ON user_activity_log FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own preferences" ON user_preferences FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Users can manage own notes" ON opportunity_notes FOR ALL USING (auth.uid() = user_id);

-- Team policies (members can view team data)
CREATE POLICY "Team members can view team" ON user_teams FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM team_members 
        WHERE team_id = user_teams.id AND user_id = auth.uid()
    )
);

CREATE POLICY "Team owners can manage team" ON user_teams FOR ALL USING (auth.uid() = owner_id);

CREATE POLICY "Team members can view members" ON team_members FOR SELECT USING (
    EXISTS (
        SELECT 1 FROM team_members tm 
        WHERE tm.team_id = team_members.team_id AND tm.user_id = auth.uid()
    )
);

-- Functions for user management
CREATE OR REPLACE FUNCTION create_user_profile()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO user_profiles (id, full_name)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name');
    
    INSERT INTO user_preferences (user_id)
    VALUES (NEW.id);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to create profile when user signs up
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION create_user_profile();

-- Function to update user activity
CREATE OR REPLACE FUNCTION log_user_activity(
    activity_type TEXT,
    activity_data JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_activity_log (user_id, activity_type, activity_data)
    VALUES (auth.uid(), activity_type, activity_data);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Function to get user dashboard stats
CREATE OR REPLACE FUNCTION get_user_dashboard_stats(user_uuid UUID)
RETURNS JSONB AS $$
DECLARE
    result JSONB;
BEGIN
    SELECT jsonb_build_object(
        'total_favorites', (SELECT COUNT(*) FROM user_favorites WHERE user_id = user_uuid AND NOT is_archived),
        'saved_searches', (SELECT COUNT(*) FROM saved_searches WHERE user_id = user_uuid AND is_active),
        'recent_activity', (SELECT COUNT(*) FROM user_activity_log WHERE user_id = user_uuid AND created_at > NOW() - INTERVAL '7 days'),
        'profile_completion', (
            SELECT CASE 
                WHEN full_name IS NOT NULL AND company IS NOT NULL AND role IS NOT NULL THEN 100
                WHEN full_name IS NOT NULL AND (company IS NOT NULL OR role IS NOT NULL) THEN 75
                WHEN full_name IS NOT NULL THEN 50
                ELSE 25
            END
            FROM user_profiles WHERE id = user_uuid
        )
    ) INTO result;
    
    RETURN result;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Update triggers for updated_at columns
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_saved_searches_updated_at BEFORE UPDATE ON saved_searches FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_opportunity_notes_updated_at BEFORE UPDATE ON opportunity_notes FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_user_teams_updated_at BEFORE UPDATE ON user_teams FOR EACH ROW EXECUTE FUNCTION update_updated_at_column(); 