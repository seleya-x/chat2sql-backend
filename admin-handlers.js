// Admin API handlers for Supabase Auth
const express = require('express');
const { createClient } = require('@supabase/supabase-js');
require('dotenv').config();

const router = express.Router();

// Log environment variables (without exposing sensitive values)
console.log('Environment check:');
console.log('- SUPABASE_URL:', process.env.SUPABASE_URL ? 'defined' : 'undefined');
console.log('- SUPABASE_SERVICE_ROLE_KEY:', process.env.SUPABASE_SERVICE_ROLE_KEY ? 'defined' : 'undefined');

// Validate required environment variables
if (!process.env.SUPABASE_URL || !process.env.SUPABASE_SERVICE_ROLE_KEY) {
  console.error('ERROR: Missing required environment variables for Supabase');
  console.error('Make sure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are defined in .env');
}

// Create a Supabase client with the service role key
const supabaseAdmin = createClient(
  process.env.SUPABASE_URL || 'https://funaizcaqsbhxafbmmyq.supabase.co',
  process.env.SUPABASE_SERVICE_ROLE_KEY || ''
);

// Verify the Supabase client
console.log('Supabase admin client initialized:', !!supabaseAdmin);

// Temporary bypass authentication for debugging
const authenticateJWT = async (req, res, next) => {
  console.log('Authentication middleware called');
  
  // For debugging only - bypass authentication
  req.user = {
    id: 'debug-user',
    email: 'debug@example.com',
    app_metadata: { role: 'admin' }
  };
  
  console.log('Debug authentication bypassed, proceeding as admin');
  next();
};

// Temporary bypass admin verification for debugging
const verifyAdmin = async (req, res, next) => {
  console.log('Admin verification middleware called');
  console.log('Debug: Bypassing admin verification');
  next();
};

// Apply the authentication and admin verification middleware to all routes
router.use(authenticateJWT);
router.use(verifyAdmin);

// Get all users
router.get('/users', async (req, res) => {
  try {
    console.log('Fetching users from Supabase Auth...');
    
    // Fetch users from Supabase Admin API
    const { data, error } = await supabaseAdmin.auth.admin.listUsers();
    
    if (error) {
      console.error('Supabase error:', error);
      return res.status(500).json({ error: 'Failed to fetch users from Supabase: ' + error.message });
    }
    
    if (!data || !data.users) {
      console.error('Invalid response format from Supabase:', data);
      return res.status(500).json({ error: 'Invalid response format from Supabase' });
    }
    
    console.log(`Successfully fetched ${data.users.length} users from Supabase`);
    
    // Format users consistently for frontend
    const formattedUsers = data.users.map(user => {
      return {
        id: user.id,
        email: user.email,
        created_at: user.created_at,
        app_metadata: user.app_metadata || {},
        user_metadata: user.user_metadata || {}
      };
    });
    
    // Return a properly formatted JSON response with real users
    return res.status(200).json({ users: formattedUsers });
  } catch (error) {
    console.error('Error fetching users from Supabase:', error);
    return res.status(500).json({ error: 'Internal server error: ' + (error.message || 'Unknown error') });
  }
});

// Create a new user
router.post('/users', async (req, res) => {
  try {
    const { email, password, user_metadata, app_metadata, email_confirm } = req.body;
    
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' });
    }
    
    console.log('Creating user with data:', {
      email,
      password: '********', // Don't log actual password
      user_metadata,
      app_metadata,
      email_confirm
    });
    
    // Ensure proper structure for metadata
    const userData = {
      email,
      password,
      email_confirm: email_confirm !== undefined ? email_confirm : true,
    };
    
    if (user_metadata) {
      userData.user_metadata = user_metadata;
    }
    
    if (app_metadata) {
      userData.app_metadata = app_metadata;
    }
    
    const { data, error } = await supabaseAdmin.auth.admin.createUser(userData);
    
    if (error) {
      console.error('Supabase error creating user:', error);
      return res.status(400).json({ error: error.message });
    }
    
    res.status(201).json({ user: data.user });
  } catch (error) {
    console.error('Error creating user:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Update a user
router.put('/users/:id', async (req, res) => {
  try {
    const { id } = req.params;
    const { email, password, user_metadata, app_metadata, email_confirm } = req.body;
    
    // Prepare update data (only include provided fields)
    const updateData = {};
    if (email) updateData.email = email;
    if (password) updateData.password = password;
    if (user_metadata) updateData.user_metadata = user_metadata;
    if (app_metadata) updateData.app_metadata = app_metadata;
    if (email_confirm !== undefined) updateData.email_confirm = email_confirm;
    
    const { data, error } = await supabaseAdmin.auth.admin.updateUserById(
      id,
      updateData
    );
    
    if (error) {
      return res.status(400).json({ error: error.message });
    }
    
    res.json({ user: data.user });
  } catch (error) {
    console.error('Error updating user:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Delete a user
router.delete('/users/:id', async (req, res) => {
  try {
    const { id } = req.params;
    
    const { error } = await supabaseAdmin.auth.admin.deleteUser(id);
    
    if (error) {
      return res.status(400).json({ error: error.message });
    }
    
    res.json({ success: true, message: 'User deleted successfully' });
  } catch (error) {
    console.error('Error deleting user:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Reset user password
router.post('/users/:id/reset-password', async (req, res) => {
  try {
    const { id } = req.params;
    const { password } = req.body;
    
    if (!password) {
      return res.status(400).json({ error: 'Password is required' });
    }
    
    const { data, error } = await supabaseAdmin.auth.admin.updateUserById(
      id,
      { password }
    );
    
    if (error) {
      return res.status(400).json({ error: error.message });
    }
    
    res.json({ success: true, message: 'Password reset successfully' });
  } catch (error) {
    console.error('Error resetting password:', error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

module.exports = router;
