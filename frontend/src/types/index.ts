export interface Message {
  id: string
  content: string
  role: 'user' | 'assistant'
  timestamp: Date
  sender?: string
}

export interface BotConfig {
  name: string
  icon_url: string
  description: string
  welcome: string
}

export interface ChatRequest {
  message: string
  user_id: string
  conversation_id?: string
}

export interface ConversationResponse {
  success: boolean
  conversation_id?: string
  error?: string
}

export interface Product {
  id: string
  name: string
  price: string
  image: string
  badge?: string
  badgeType?: 'hot' | 'new' | 'premium'
}
