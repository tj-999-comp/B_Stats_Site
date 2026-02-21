export type Database = {
  public: {
    Tables: {
      player_stats: {
        Row: {
          id: number;
          season: string;
          player_name: string;
          team_name: string;
          games_played: number;
          points: number;
          rebounds: number;
          assists: number;
          steals: number;
          blocks: number;
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database['public']['Tables']['player_stats']['Row'], 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Database['public']['Tables']['player_stats']['Insert']>;
      };
      team_stats: {
        Row: {
          id: number;
          season: string;
          team_name: string;
          wins: number;
          losses: number;
          win_rate: number;
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database['public']['Tables']['team_stats']['Row'], 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Database['public']['Tables']['team_stats']['Insert']>;
      };
      rankings: {
        Row: {
          id: number;
          season: string;
          rank: number;
          team_name: string;
          conference: string;
          created_at: string;
          updated_at: string;
        };
        Insert: Omit<Database['public']['Tables']['rankings']['Row'], 'id' | 'created_at' | 'updated_at'>;
        Update: Partial<Database['public']['Tables']['rankings']['Insert']>;
      };
    };
  };
};
